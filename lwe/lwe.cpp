#include <iostream>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;


py::array_t<int, 32> encode(const std::string &message, int addition) {
    int size = message.size();
    auto array = py::array_t<int, 32>(size);
    py::buffer_info buffer = array.request(true);
    int* array_ptr = static_cast<int *>(buffer.ptr);

    for (int i = 0; i < size; i++) {
        array_ptr[i] = (int)message[i] * addition;
    }

    return array;
}


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
    handle.def("encode", &encode);
}