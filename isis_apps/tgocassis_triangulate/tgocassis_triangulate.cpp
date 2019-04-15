#include "Isis.h"
#include "ProcessByLine.h"
#include "SpecialPixel.h"


#include <Table.h> 
#include <Brick.h>
#include "Camera.h"
#include "Projection.h"
#include "TProjection.h"

#include <unordered_map>
#include <dirent.h> 
#include <stdio.h> 
#include <regex>
#include <iostream>
#include <string>

#include "gdal_priv.h"


#define SUB2IDX_2D(x, y, width) ((y) * (width) + (x)) 

using namespace std;
using namespace Isis;


#define FLOAT_MIN -16777215

void preloadCubes(const char* dirname, unordered_map<string, Cube*> &cubes)
{
  
  DIR *dirp;
  struct dirent *directory;
  dirp = opendir(dirname);
  cout << "preloading cubes from : " << dirname << endl;
  if (dirp)
  {
      while ((directory = readdir(dirp)) != NULL)
      {

        string filename = string(dirname) + "/" + string(directory->d_name);
        // check if file looks like cube
        if ( regex_match(filename, std::regex(".+cub") ) )
        {
          Cube *pCube = new Cube(QString::fromStdString(filename));
          cubes[string(directory->d_name)] = pCube;
          #ifdef DEBUG_MSG 
           printf("   %s/%s\n", dirname, directory->d_name);
          #endif
        }
      }
      closedir(dirp);
  }
  
}

// Prototype a FORTRAN function here. 
extern "C" void xvector_m__( double* , double* ,        /* Vector that contains two origins */ 
     double* , double* ,    /* Vector that contains two directions */
     double* ,         /* Output point  */ 
     double* ,         /* Output error  */ 
     int*  );           /* Output status */

// given sample and line in mosaic, function return name of responsible cube
int getCubeFilename(int sample, int line, Cube *pCub, QString &fileName)
{
  
  // read table cubes names
  Table tab("InputImages");
  pCub->read(tab);
  
  // get trace value from mosaic cube 
  Brick pixel(1, 1, 1, Isis::Real);
  pixel.SetBasePosition(sample, line, 2); // sample, line and band are '1'-based 
  pCub->read(pixel);
  
  if (pixel[0] == -8388613) return 1;
  int tab_idx = pixel[0] - FLOAT_MIN;

  // get cube name
  fileName = QString( tab[tab_idx][0] );

  return 0;
}


bool readGeotiff(string filename, int &width, int &height, vector<float> &dispx, vector<float> &dispy, vector<float> &mask)
{

  GDALAllRegister();
  GDALDataset  *pDataset = (GDALDataset*) GDALOpen( filename.c_str(), GA_ReadOnly );
  
  GDALRasterBand *dispx_band = pDataset->GetRasterBand( 1 );
  GDALRasterBand *dispy_band = pDataset->GetRasterBand( 2 );
  GDALRasterBand *mask_band = pDataset->GetRasterBand( 3 );
  
  width  = dispx_band->GetXSize();
  height = dispx_band->GetYSize();
  int vol = width*height;

  // resize vector to accomodate image
  dispx.resize(vol);
  dispy.resize(vol);
  mask.resize(vol);
    
  // vector standard garantees that elements placed continuously 
  GDALRasterIO( dispx_band, GF_Read, 0, 0, width, height, &dispx[0], width, height, GDT_Float32, 0, 0 );   
  GDALRasterIO( dispy_band, GF_Read, 0, 0, width, height, &dispy[0], width, height, GDT_Float32, 0, 0 );   
  GDALRasterIO( mask_band, GF_Read, 0, 0, width, height, &mask[0], width, height, GDT_Float32, 0, 0 );   

  #ifdef DEBUG_MSG 
     cout << "Read geotiff file (" << width << "x" << height << "). " << endl;
  #endif

  GDALClose( (GDALDatasetH) pDataset );
  
  return true;
}


//#define DEBUG_MSG
void IsisMain() {

  Process p;

  UserInterface ui = Application::GetUserInterface();

  // Read geotiff with disparities
  vector<float> dispx;
  vector<float> dispy;
  vector<float> mask;
  int width, height;
  readGeotiff( ui.GetFileName("DISPARITY").toStdString(), width, height, dispx, dispy, mask );

  // Read mosaic cubes
  Cube* pMosaic0 = p.SetInputCube("MOSAIC_0");
  Cube* pMosaic1 = p.SetInputCube("MOSAIC_1");
    
  // Read corresponding projections
  TProjection *pProj0 = (TProjection *) pMosaic0->projection();
  TProjection *pProj1 = (TProjection *) pMosaic1->projection();

  // Read map-projected framelets folder
  string mapproj_framelet0_dn = ui.GetFileName("FRAMELETS_0").toStdString();
  string mapproj_framelet1_dn = ui.GetFileName("FRAMELETS_1").toStdString();
 
  // Load all cubes from specified folders to hash table
  unordered_map<string, Cube*> mapproj_framelets0;
  preloadCubes(mapproj_framelet0_dn.c_str(), mapproj_framelets0);

  unordered_map<string, Cube*> mapproj_framelets1;
  preloadCubes(mapproj_framelet1_dn.c_str(), mapproj_framelets1);

  // Make output cube with digital elevation model.
  int samps = pMosaic0->sampleCount();
  int lines = pMosaic0->lineCount();
  CubeAttributeOutput &dtm_attribute = ui.GetOutputAttribute("DTM");
  QString dtm_file = ui.GetFileName("DTM");
  Cube* pElev = p.SetOutputCube(dtm_file, dtm_attribute, samps, lines, 1);
  
  // Make output cube with triangulation error.
  CubeAttributeOutput &error_attribute = ui.GetOutputAttribute("ERROR");
  QString error_file = ui.GetFileName("ERROR");
  Cube* pTriangulationError = p.SetOutputCube(error_file, error_attribute, samps, lines, 1);
  
  // Allocate space for distances
  // we use it to perform nn-interpolation
  vector<float> dist;
  dist.resize(width*height, HUGE_VALF );
  
  // Go through all pixels. 
  // Note that lines and samples in geotiff file are 0-based,
  // but in ISIS they start from 0.5 
  int i = 0;
  for(int line0   = 0; line0 < height; line0++)
  for(int sample0 = 0; sample0 < width; sample0++)
  {
    
    #ifndef  DEBUG_MSG 
    if (i % 1000 == 0){
      cout << "Triangulation Progress " << 100 * float(i) / float(width*height) << "%" << std::flush;
      cout << "\r";
    }
    i++;
    #endif
    
    float mask0 = mask[SUB2IDX_2D(sample0, line0, width)];
    if( mask0 == 0 ) continue; 
    float dispx0 = dispx[SUB2IDX_2D(sample0, line0, width)];
    float dispy0 = dispy[SUB2IDX_2D(sample0, line0, width)];        
    

    // compute matching line sample in two image
    float line1 = (float)line0 + dispy0;
    float sample1 = (float)sample0 + dispx0;

    #ifdef DEBUG_MSG 
    cout << "line0=" << line0 << " sample0=" << sample0 << " line1=" << line1 << " sample1=" << sample1 << endl;
    cout << "dispx=" << dispx0 << " dispy=" << dispy0 << " mask=" << mask0 << endl;
    #endif

    // in isis line, sample start from 0.5
    float line1_isis = (float)line1 + 0.5;
    float line0_isis = (float)line0 + 0.5;
    float sample0_isis = (float)sample0 + 0.5;
    float sample1_isis = (float)sample1 + 0.5;
      
    // 1st point
    // lon, lat and responsible cube
    #ifdef DEBUG_MSG 
    cout << "  mosaic0 : " << endl;
    #endif
    QString framelet0_fn;
    pProj0->SetWorld( sample0_isis, line0_isis );
    if ( !pProj0->IsGood() ) continue; // error!
    // note that here sample and line positions are 1-based
    if (getCubeFilename( (int)ceil(sample0_isis), (int)ceil(line0_isis), pMosaic0, framelet0_fn)) continue; // error!
    Cube *pCub0 = mapproj_framelets0[framelet0_fn.toStdString()];
    float lat0 = pProj0->UniversalLatitude();
    float lon0 = pProj0->UniversalLongitude();
    #ifdef DEBUG_MSG 
    cout << "     responsible : " << framelet0_fn.toStdString() << endl;
    cout << "     lon=" << lon0 << " lat=" << lat0 << endl;
    #endif

    // instrument position and pointing
    Camera *pCam0 = pCub0->camera();
    pCam0->SetUniversalGround( lat0, lon0 );
    if ( !pCam0->HasSurfaceIntersection() ) continue;
    vector<double> dir0;
    double pos0[3]; 
    dir0 = pCam0->lookDirectionBodyFixed();
    pCam0->instrumentPosition( pos0 );
    #ifdef DEBUG_MSG 
    cout << "     dir : " << dir0[0] << " " << dir0[1] << " " << dir0[2] << endl;
    cout << "     pos : " << pos0[0] << " " << pos0[1] << " " << pos0[2] << endl;
    #endif

    // 2nd point
    // lon, lat and responsible cube
    #ifdef DEBUG_MSG 
    cout << "  mosaic1 : " << endl;
    #endif
    QString framelet1_fn;
    pProj1->SetWorld( sample1_isis, line1_isis );
    if ( !pProj1->IsGood() ) continue; // error!
    if (getCubeFilename( (int)ceil(sample1_isis), (int)ceil(line1_isis), pMosaic1, framelet1_fn)) continue; // error!
    Cube *pCub1 = mapproj_framelets1[framelet1_fn.toStdString()];
    float lat1 = pProj1->UniversalLatitude();
    float lon1 =  pProj1->UniversalLongitude();
    #ifdef DEBUG_MSG 
    cout << "     responsible : " << framelet1_fn.toStdString() << endl;
    cout << "     lon=" << lon1 << " lat=" << lat1 << endl;
    #endif
    
    // instrument position and pointing
    Camera *pCam1 = pCub1->camera();
    pCam1->SetUniversalGround( lat1, lon1 );
    if ( !pCam1->HasSurfaceIntersection() ) continue;
    vector<double> dir1;
    double pos1[3]; 
    dir1 = pCam1->lookDirectionBodyFixed();
    pCam1->instrumentPosition( pos1 );
    #ifdef DEBUG_MSG 
    cout << "     dir : " << dir1[0] << " " << dir1[1] << " " << dir1[2] << endl;
    cout << "     pos : " << pos1[0] << " " << pos1[1] << " " << pos1[2] << endl;
    #endif

    double point[3], error; 
    int status;
    xvector_m__( pos0, &dir0[0], pos1, &dir1[0], point, &error, &status ); 
    
    #ifdef DEBUG_MSG 
    cout << "  intersection body fixed: " << point[0] << " " << point[1] << " " << point[2] << endl;
    #endif

    // compute planetocentric coordinates (lat, lon, range) using spice
    // note that (1) SPICE computes  lat / lon in radiance, but we want degrees
    //           (2) SPICE computes longitude can be negative, but we want it [0 360]
    double xLat, xLon, xRange; 
    reclat_c(point, &xRange, &xLon, &xLat ); 
    xLon = xLon * dpr_c(); 
    xLat = xLat * dpr_c();
    xLon = (xLon < 0) ? (xLon + 360) : (xLon);  

    #ifdef DEBUG_MSG 
    cout << "  intersection planetocentric: range=" << xRange << " lon=" << xLon << " lat=" << xLat << endl;
    #endif
        
    // compute elevation with respect to mars ellipsoid
    double MARSRAD[3] = { 3396.19, 3396.19, 3376.20 } ; 
    double xElev;
    double surfPoint[3];
    nearpt_c(point, MARSRAD[0], MARSRAD[1], MARSRAD[2], surfPoint, &xElev ); 
    xElev *= 1000; // we want elevation in meters 

    #ifdef DEBUG_MSG 
    cout << "  intersection planetocentric: elevaton=" << xElev << endl;
    cout << "  closest surfcae point: " << surfPoint[0] << " " << surfPoint[1] << " " << surfPoint[2] << " " << endl;
    #endif

    // Compute sample / line position in map-projected
    pProj0->SetUniversalGround(xLat, xLon);
    if( pProj0->IsGood() ){

      float xLine   = pProj0->WorldY() + 0.5;  // 1-based
      float xSample = pProj0->WorldX() + 0.5;

      // Record triangulation error.
      Brick pixel(1, 1, 1, Isis::Real);
      pixel.SetBasePosition(xSample, xLine, 1); // 1-based 
      pixel[0] = error;
      pTriangulationError->write(pixel);

      for( int dline = 0; dline <= 1; dline++ )
      for( int dsample = 0; dsample <= 1; dsample++ )
      {
        float cLine =  floor(xLine) + (float)dline; // 1-based
        float cSample = floor(xSample) + (float)dsample;
        float cDist = (cLine-xLine)*(cLine-xLine) + (cSample-xSample)*(cSample-xSample); 
        if (dist[SUB2IDX_2D((int)cSample-1, (int)cLine-1, width)] > cDist) // 0-based
        {
           dist[SUB2IDX_2D((int)cSample-1, (int)cLine-1, width)] = cDist;  // 0-based
           Brick pixel(1, 1, 1, Isis::Real);
           pixel.SetBasePosition(cSample, cLine, 1); // 1-based 
           pixel[0] = xElev;
           pElev->write(pixel);

        } 
      }  

      #ifdef DEBUG_MSG 
        cout << "  output cube line=" << xLine << " sample=" << xSample << endl;
      #endif

    }

  }

  // release all map-projected framelet cubes
  for (pair<string, Cube*> element : mapproj_framelets0) delete element.second;
  for (pair<string, Cube*> element : mapproj_framelets1) delete element.second;
    
    
  p.EndProcess();
}


