#include <iostream>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <iostream>
#include <locale>
#include <string>
#include <codecvt>
#include <vector>
#include <random>
#include <cmath>
#include <pybind11/stl.h>

namespace py = pybind11;

typedef std::vector<std::vector<long long>> matrix;

std::random_device rd;
std::wstring_convert<std::codecvt_utf8<char32_t>, char32_t> converter;




std::string _decode(py::array_t<int, 32> array) {
    std::string return_value;
    auto array_proxy = array.unchecked<1>();
    int size = array_proxy.size();

    for (int i = 0; i < size; i++) {
        return_value += (char)array_proxy(i);
    }

    return return_value;
}


std::string _decode_utf8(py::array_t<int, 32> array) {
    std::string return_value;
    auto array_proxy = array.unchecked<1>();
    int size = array_proxy.size();

    for (int i = 0; i < size; i++) {
        char32_t character = (char32_t)array_proxy(i);
        return_value += converter.to_bytes(character);
    }

    return return_value;
}


py::array_t<int, 32> encode(const std::u32string &message, int addition, int length) {
    int size = message.size();

    auto array = py::array_t<int, 32>(size);
    py::buffer_info buffer = array.request(true);
    int* array_ptr = static_cast<int *>(buffer.ptr);

    for (int i = 0; i < size; i++) {
        array_ptr[i] = (int)message[i] * addition;
    }

    return array;
}


std::string decode(py::array_t<int, 32> array, int max_value) {
    if (max_value < 128) {
        return _decode(array);
    }
    else {
        return _decode_utf8(array);
    }
}




PYBIND11_MODULE(lwe, handle) {
    handle.doc() = "LWE C++ Module";
    handle.def("decode", &decode);
    handle.def("encode", &encode);
}
