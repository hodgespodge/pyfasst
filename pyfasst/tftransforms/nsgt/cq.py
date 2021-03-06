#python
# -*- coding: utf-8

"""
Python implementation of Non-Stationary Gabor Transform (NSGT)
derived from MATLAB code by NUHAG, University of Vienna, Austria

Thomas Grill, 2011-2012
http://grrrr.org/nsgt

Austrian Research Institute for Artificial Intelligence (OFAI)
AudioMiner project, supported by Vienna Science and Technology Fund (WWTF)

--
Original matlab code copyright follows:

AUTHOR(s) : Monika Dörfler, Gino Angelo Velasco, Nicki Holighaus, 2010-2011

COPYRIGHT : (c) NUHAG, Dept.Math., University of Vienna, AUSTRIA
http://nuhag.eu/
Permission is granted to modify and re-distribute this
code in any manner as long as this notice is preserved.
All standard disclaimers apply.

"""

import numpy as N
from .nsgfwin_sl import nsgfwin
from .nsdual import nsdual
from .nsgtf import nsgtf
from .nsigtf import nsigtf
from .util import calcwinrange
from .fscale import OctScale

class NSGT:
    def __init__(self,scale,fs,Ls,real=True,measurefft=False,matrixform=False,reducedform=0,multichannel=False):
        assert fs > 0
        assert Ls > 0
        assert 0 <= reducedform <= 2
        
        self.scale = scale
        self.fs = fs
        self.Ls = Ls
        self.real = real
        self.measurefft = measurefft
        self.reducedform = reducedform
        
        self.frqs,self.q = scale()

        # calculate transform parameters
        self.g,rfbas,self.M = nsgfwin(self.frqs,self.q,self.fs,self.Ls,sliced=False)

        if matrixform:
            if self.reducedform:
                rm = self.M[self.reducedform:len(self.M)//2+1-self.reducedform]
                self.M[:] = rm.max()
            else:
                self.M[:] = self.M.max()
    
        if multichannel:
            self.channelize = lambda s: s
            self.unchannelize = lambda s: s
        else:
            self.channelize = lambda s: (s,)
            self.unchannelize = lambda s: s[0]
            
        # calculate shifts
        self.wins,self.nn = calcwinrange(self.g,rfbas,self.Ls)
        # calculate dual windows
        self.gd = nsdual(self.g,self.wins,self.nn,self.M)
        
        self.fwd = lambda s: nsgtf(s,self.g,self.wins,self.nn,self.M,real=self.real,reducedform=self.reducedform,measurefft=self.measurefft)
        self.bwd = lambda c: nsigtf(c,self.gd,self.wins,self.nn,self.Ls,real=self.real,reducedform=self.reducedform,measurefft=self.measurefft)
        

    def forward(self,s):
        'transform'
        s = self.channelize(s)
        c = list(map(self.fwd,s))
        return self.unchannelize(c)

    def backward(self,c):
        'inverse transform'
        c = self.channelize(c)
        s = list(map(self.bwd,c))
        return self.unchannelize(s)
    
class CQ_NSGT(NSGT):
    def __init__(self,fmin,fmax,bins,fs,Ls,real=True,measurefft=False,matrixform=False,reducedform=0,multichannel=False):
        assert fmin > 0
        assert fmax > fmin
        assert bins > 0
        
        self.fmin = fmin
        self.fmax = fmax
        self.bins = bins

        scale = OctScale(fmin,fmax,bins)
        NSGT.__init__(self,scale,fs,Ls,real,measurefft,matrixform,reducedform,multichannel)


import unittest
norm = lambda x: N.sqrt(N.sum(N.abs(N.square(x))))

class TestNSGT(unittest.TestCase):

    def setUp(self):
        pass

    def test_oct(self):
        for _ in range(100):
            sig = N.random.random(100000)
            fmin = N.random.random()*200+1
            fmax = N.random.random()*(22048-fmin)+fmin
            obins = N.random.randint(24)+1
            print(fmin,fmax,obins)
            scale = OctScale(fmin,fmax,obins)
            nsgt = NSGT(scale,fs=44100,Ls=len(sig))
            c = nsgt.forward(sig)
            s_r = nsgt.backward(c)
            rec_err = norm(sig-s_r)/norm(sig)
            self.assertAlmostEqual(rec_err,0)

if __name__ == '__main__':
    unittest.main()
