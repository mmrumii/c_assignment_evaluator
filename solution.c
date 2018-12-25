#include<stdio.h>
#include<stdlib.h>

int adder(int x, int y){
	int result = x + y;
	return result;
};

int main(int argc,char* argv[]){
	int a = atoi(argv[1]);
	int b = atoi(argv[2]);
	int sum = adder(a,b);
	printf("%d",sum);
	return 0;
};