      subroutine xvector_m( Origin1, Vector1, Origin2, Vector2,
     $                      Point, Error, Status )
      
      implicitnone

C     NAME : xvector_m
C
C     PURPOSE : 
C     Finds the closest point between two rays. Usually used to find
C     intersection of two rays in image stereo pair. 
C     
C     This subroutine is a little modified version of Jean Lorre's
C     xvector routine that takes rays as inputs. Jean's routine takes
C     camera information as inputs. In principle it is possible to
C     merge the two routines. 
C
C     REFERENCE : Manual of Photogrammetry, page 64.
C
C     CALLING SEQUENCE
C       call xvector_m( Origin1, Vector1, Origin2, Vector2
C     $                 Point, Error, Status ) 
C
C     INPUTS 
C
C     Origin and direction of vector 1
      DOUBLE PRECISION         Origin1(3)
      DOUBLE PRECISION         Vector1(3)

C     Origin and direction of vector 2
      DOUBLE PRECISION         Origin2(3)
      DOUBLE PRECISION         Vector2(3)
        
C     OUTPUTS
C
C     Intersection point
      DOUBLE PRECISION          Point(3)
C      
C     Error or miss distance
      DOUBLE PRECISION          Error
C
C     Status of the algorithm - whether a convergence was found
C     0 - everything OK, 1 - algorithm did not converge. 
      INTEGER                   Status
C
C
C     EXAMPLE
C      program tstxvector_m
C C    Camera positions
C      double precision cam1(3)
C      double precision cam2(3)
C      
C C    Camera directions
C      double precision uvw1(3)
C      double precision uvw2(3)

C C    Results 
C      double precision point(3)
C      double precision error
C      integer status
C
c      DATA cam1 /0.0, 0.0, 0.0/
c      DATA cam2 /10.0, 0.0, 0.0/
c      DATA uvw1 / 0.707107, 0.707107, 0.0 /
c      DATA uvw2 /-0.707107, 0.707107, 0.0001 /
C
C      call xvector_m( cam1, uvw1, cam2, uvw2, point, error, status )
C      end 
C C         --------------- end example --------------------
C
C     HISTORY
C       Code extracted from lstoxyz.f - 12-Jun-2001. 
C       $Log: xvector_m.f,v $
C       Revision 1.1  2001/06/12 20:39:54  abi
C       Initial revision
C
C
C     Internal variables 
C     
C     Ray coordinates mapped into original Jean's variables
      DOUBLE PRECISION          u1, v1, w1
      DOUBLE PRECISION          u2, v2, w2

C     Camera position in space 
      DOUBLE PRECISION          cam1(3)
      DOUBLE PRECISION          cam2(3)

C     Other variables needed for solution
      DOUBLE PRECISION          as, bs, cs
      DOUBLE PRECISION          as1, bs1, cs1
      DOUBLE PRECISION          as2, bs2, cs2

C     Setup matrices 
      DOUBLE PRECISION          a(9), b(3), c(9)
      
C     Intermediate variables 
      DOUBLE PRECISION          x, y, z
      DOUBLE PRECISION          xx, yy, zz

C     Counter variable
      INTEGER                   i

C     ----------------------------- End header -------------------

C     Initialize status variable to NOT OK. 
      status = 1

C     Map input parameters into this subroutine variables. 
      u1 = Vector1(1)
      v1 = Vector1(2)
      w1 = Vector1(3)
      
      u2 = Vector2(1)
      v2 = Vector2(2)
      w2 = Vector2(3)
      
      do 1001 i = 1, 3
         cam1(i) = Origin1(i)
         cam2(i) = Origin2(i)
 1001 end do

C     solve for x,y,z point on ray1 nearest to ray2
      as=v1*w2-w1*v2
      bs=u2*w1-u1*w2
      cs=u1*v2-v1*u2
      as1=bs*w1-v1*cs
      bs1=u1*cs-as*w1
      cs1=as*v1-u1*bs
      as2=bs*w2-v2*cs
      bs2=u2*cs-as*w2
      cs2=as*v2-u2*bs
      a(1)=as
      a(2)=as1
      a(3)=as2
      a(4)=bs
      a(5)=bs1
      a(6)=bs2
      a(7)=cs
      a(8)=cs1
      a(9)=cs2
      do 10 i=1,9
         c(i)=a(i)
 10   continue
      b(1)=as*cam1(1)+bs*cam1(2)+cs*cam1(3)
      b(2)=as1*cam1(1)+bs1*cam1(2)+cs1*cam1(3)
      b(3)=as2*cam2(1)+bs2*cam2(2)+cs2*cam2(3)
      call dp_dsimq(a,b,3, Status)
      x=b(1)
      y=b(2)
      z=b(3)
      if( Status .gt. 0) return

c solve for xx,yy,zz point on ray2 nearest to ray1
      b(1)=as*cam2(1)+bs*cam2(2)+cs*cam2(3)
      b(2)=as1*cam1(1)+bs1*cam1(2)+cs1*cam1(3)
      b(3)=as2*cam2(1)+bs2*cam2(2)+cs2*cam2(3)
      call dp_dsimq(c,b,3, Status)
      if( Status .gt. 0) return
      xx=b(1)
      yy=b(2)
      zz=b(3)
      
c point inbetween is the closest approach point to both vectors
       error=dsqrt((z-zz)**2+(y-yy)**2+(x-xx)**2)
       point(1) = (x+xx)/2.d0
       point(2) = (y+yy)/2.d0
       point(3) = (z+zz)/2.d0

      
       return
       end     


      
      
