"""Building the Quest backend from C code"""
# Copyright 2019 HQS Quantum Simulations GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ctypes
from cffi import FFI
import os
import platform


def build_quest_so():
    lib_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pyquest_cffi/questlib/')
    quest_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "QuEST/QuEST")
    if platform.system() == 'Darwin':
        questlib = os.path.join(lib_path, "libQuEST.dylib")
    else:
        questlib = os.path.join(lib_path, "libQuEST.so")
    include = [os.path.join(quest_path, "include")]

    _questlib = ctypes.CDLL(questlib)
    QuESTPrecFunc = _questlib['getQuEST_PREC']
    QuESTPrecFunc.restype = ctypes.c_int
    QuESTPrec = QuESTPrecFunc()

    if QuESTPrec == 1:
        qreal = "float"
    elif QuESTPrec == 2:
        qreal = "double"
    elif QuESTPrec == 4:
        qreal = "longdouble"
    else:
        raise TypeError('Unable to determine precision of qreal')
    del(QuESTPrec)
    del(QuESTPrecFunc)

    with open(os.path.join(include[0], "QuEST.h"), "r") as f:
        lines = [line for line in f]

    lines += ["void statevec_setAmps(Qureg qureg, long long int startInd,"
              + " qreal* reals, qreal* imags, long long int numAmps);"]
    lines += ["qreal densmatr_calcProbOfOutcome(Qureg qureg, const int measureQubit, int outcome);"]
    lines += ["qreal statevec_calcProbOfOutcome(Qureg qureg, const int measureQubit, int outcome);"]
    lines += ["int generateMeasurementOutcome(qreal zeroProb, qreal *outcomeProb);"]
    lines += ["int getQuEST_PREC(void);"]

    _lines = []
    no_def = True
    skip = False
    for line in lines:
        if not line.find("getEnvironmentString") >= 0:
            if skip:
                if line.startswith('#endif'):
                    skip = False
            elif line.startswith('#ifndef __cplusplus'):
                skip = True
            elif no_def and not line.startswith("#"):
                _lines.append(line)
            elif line.startswith("#ifdef"):
                no_def = False
            elif line.startswith("#endif"):
                no_def = True
    _lines = "".join(_lines).replace('qreal', qreal)

    ffibuilder = FFI()
    ffibuilder.cdef(_lines)
    ffibuilder.set_source(
        "_quest", r'''
            #include <QuEST.h>
        ''',
        libraries=["QuEST"],
        include_dirs=include,
        library_dirs=[lib_path],
        extra_link_args=['-Wl,-rpath,$ORIGIN'],
        # extra_link_args=['-Wl,-rpath={}'.format(lib_path)],
    )
    ffibuilder.compile(verbose=True)


if __name__ == '__main__':
    build_quest_so()
