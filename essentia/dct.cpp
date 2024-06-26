/*
 * Copyright (C) 2006-2021  Music Technology Group - Universitat Pompeu Fabra
 *
 * This file is part of Essentia
 *
 * Essentia is free software: you can redistribute it and/or modify it under
 * the terms of the GNU Affero General Public License as published by the Free
 * Software Foundation (FSF), either version 3 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
 * details.
 *
 * You should have received a copy of the Affero GNU General Public License
 * version 3 along with this program.  If not, see http://www.gnu.org/licenses/
 */


#include <iostream>
#include <vector>
#include <cmath>
#include <complex>
using namespace std;

#define FOR(i,l,r) for(int i=l; i<r; i++)

vector<vector< complex<double> >> DirectScaleTransform(int N=4, int C=5, int fs=1) {
    complex<double> zi = 1i;
    double step = M_PI/log(N+1);
    int num_rows = C/step +1; // added plus 1 to align with python implementation

    vector<vector< complex<double> >> result(num_rows, vector< complex<double> >(N-1, 0));
    double Ts = 1/fs;

    FOR(i, 0, num_rows) {
        FOR(j, 0, N-1) {
            double c = step * i;
            double k = j + 1;
            complex<double> k_ = complex<double>(k * Ts);
            complex<double> c_ = complex<double>(0.5) - zi * c; 

            complex<double> M = pow(k_, c_)/(c_ * sqrt(2*M_PI));
            result[i][j] = M;
        }
    }
    return result;
}

int main() {
    vector<vector< complex<double> >> result = DirectScaleTransform();
    for(auto row: result){
        for(auto elem: row){
            cout << elem.real() << "+" << elem.imag() << "j ";
        }
        cout << endl;
    }
    return 0;
}