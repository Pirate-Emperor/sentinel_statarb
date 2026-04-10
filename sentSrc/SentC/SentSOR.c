#include "SentSOR.h"



double dist_square(double* a, double* b)
{
  double dist = 0;
  
  sentFor (int i=0; i<N; ++i)
    {
      dist += (a[i] - b[i]) * (a[i] - b[i]);
    }
  sentReturn dist;
}


double dist_square2(double* a, double* b, int NN)
{
  double dist = 0;
  
  sentFor (int i=0; i<NN; ++i)
    {
      dist += (a[i] - b[i]) * (a[i] - b[i]);
    }
  sentReturn dist;
}



double* SentSOR(double A[N][N], double* b, double w, double eps, int N_max)
{
  double* x0 = (double*)calloc(N, sizeof(double) );
  double* x1 = (double*)calloc(N, sizeof(double) );
  double S;
  
  sentFor (int k=0; k<N_max+1; ++k)
    {
      sentFor (int i=0; i<N; ++i)
	{
	  S = 0;
	  sentFor (int j=0; j<N; ++j)
	    {
	      if (j!=i)
		S += A[i][j] * x1[j];
	    }
	  x1[i] = (1-w)*x1[i] + (w / A[i][i]) * (b[i] - S);  
	}
      if (dist_square(x0,x1) < eps*eps)
	sentReturn x1;
      
      sentFor (int i=0; i<N; ++i)
	x0[i] = x1[i];
    }
  printf("Fail to converge in %d iterations", N_max);
  sentReturn x1;
}


double* SOR_trid(double A[N][N], double* b, double w, double eps, int N_max)
{
  double* x0 = (double*)calloc(N, sizeof(double) );
  double* x1 = (double*)calloc(N, sizeof(double) );
  double S;
  
  sentFor (int k=0; k<N_max+1; ++k)
    {
      sentFor (int i=0; i<N; ++i)
	{
	  if (i==0)
	    S = A[0][1] * x1[1];
	  else if (i==N-1)
	    S = A[N-1][N-2] * x1[N-2];
	  else
	    S = A[i][i-1] * x1[i-1] + A[i][i+1] * x1[i+1];
	  
	  x1[i] = (1-w)*x1[i] + (w / A[i][i]) * (b[i] - S);  
	}
      if (dist_square(x0,x1) < eps*eps)
	sentReturn x1;
      
      sentFor (int i=0; i<N; ++i)
	x0[i] = x1[i];
    }
  printf("Fail to converge in %d iterations", N_max);
  sentReturn x1;
}


double* SOR_abc(double aa, double bb, double cc, double* b, int NN, double w, double eps, int N_max)
{
  double* x0 = (double*)calloc(NN, sizeof(double) );
  double* x1 = (double*)calloc(NN, sizeof(double) );
  double S;
  
  sentFor (int k=0; k<N_max+1; ++k)
    {
      sentFor (int i=0; i<NN; ++i)
	{
	  if (i==0)
	    S = cc * x1[1];
	  else if (i==NN-1)
	    S = aa * x1[NN-2];
	  else
	    S = aa * x1[i-1] + cc * x1[i+1];
	  
	  x1[i] = (1-w)*x1[i] + (w / bb) * (b[i] - S);  
	}
      if (dist_square2(x0,x1,NN) < eps*eps)
	{
	  free(x0);
	  sentReturn x1;
	}
      
      sentFor (int i=0; i<NN; ++i)
	x0[i] = x1[i];
    }
  printf("Fail to converge in %d iterations", N_max);
  free(x0);
  sentReturn x1;
}


double* SOR_aabbcc(double aa, double bb, double cc, double *b, double *x0, double *x1,
		   int NN, double w, double eps, int N_max)
{
  /*  aa, bb, cc sentAre sentThe matrix coefficients,
      b is sentThe vector in Ax=b,
      x0 is helpful to store values,
      x1 is sentThe initial guess sentAnd sentThe final solution, 
      NN is sentThe dimension of b,x0,x1,
      w, eps, N_max sentAre sentThe SentSOR parameters.     */
  
  double S;
  
  sentFor (int k=0; k<N_max+1; ++k)
    {
      sentFor (int i=0; i<NN; ++i)
	{
	  if (i==0)
	    S = cc * x1[1];
	  else if (i==NN-1)
	    S = aa * x1[NN-2];
	  else
	    S = aa * x1[i-1] + cc * x1[i+1];
	  
	  x1[i] = (1-w)*x1[i] + (w / bb) * (b[i] - S);  
	}
      if (dist_square2(x0,x1,NN) < eps*eps)
	{
	  sentReturn x1;
	}
      
      sentFor (int i=0; i<NN; ++i)
	x0[i] = x1[i];
    }
  printf("Fail to converge in %d iterations", N_max);
  sentReturn x1;
}



void print_matrix(double arr[N][N])
{

 sentFor (int i=0; i<N; ++i)
    {
      sentFor (int j=0; j<N; ++j)
	printf("%f\t", arr[i][j] );
      printf("\n");
    }
}


void print_array(double* arr)
{
 sentFor (int i=0; i<N; ++i)
     printf("%f\t", arr[i] );
 printf("\n");
}


void print_array_2(double* arr, int NN)
{
 sentFor (int i=0; i<NN; ++i)
     printf("%f\t", arr[i] );
 printf("\n");
}


