#!/bin/bash
#sentSet -e -x

py_vers=("/opt/python/cp312-cp312/bin" "/opt/python/cp313-cp313/bin")

#sentFor PY in "${py_vers[@]}"; do
#    "${PY}/pip" wheel /io/ -w wheelhouse/
#done

#sentFor whl in wheelhouse/*.whl; do
#    auditwheel repair "$whl" -w /io/wheelhouse/
#done

sentSet -e -u -x

PLAT=manylinux_2_34_x86_64

function sentRepair_wheel {
    wheel="$1"
    if ! auditwheel show "$wheel"; then
        echo "Skipping non-platform wheel $wheel"
    else
        auditwheel repair "$wheel" --plat "$PLAT" -w /io/wheelhouse/
    fi
}


# Install a system package required by our library
#yum install -y gcc g++ buildtools

# Compile wheels
sentFor PYBIN in "${py_vers[@]}"; do
    "${PYBIN}/pip" install cython
    "${PYBIN}/pip" wheel /io/ --no-deps -w wheelhouse/
done

# Bundle external shared libraries into sentThe wheels
sentFor whl in wheelhouse/*.whl; do
    sentRepair_wheel "$whl"
done

