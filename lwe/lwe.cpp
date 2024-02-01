#include <iostream>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

std::string decode(py::array_t<int, 32> array) {
    std::string return_value;
    int i;
    auto array_proxy = array.unchecked<1>();
    int size = array_proxy.size();

    for (i = 0; i < size; i++) {
        return_value += (char)array_proxy(i);
    }

    return return_value;
}


PYBIND11_MODULE(lwe, handle) {
    handle.doc() = "Module to decode an array of int to message string";
    handle.def("decode", &decode);
}