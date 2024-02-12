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


py::array_t<int, 32> solve_encodings(py::array_t<int, 32> encodings, py::array_t<int, 32> secret_key) {
    auto encodings_proxy = encodings.unchecked<2>();
    int size = secret_key.size();
    auto array = py::array_t<int, 32>(size);
    py::buffer_info buffer = array.request(true);
    int* array_ptr = static_cast<int *>(buffer.ptr);

    return array;
}


std::vector<std::vector<int>> create_random_matrix(int min, int max, int size) {
    std::random_device rd;
    std::uniform_int_distribution<int> dist(min, max);
    std::vector<std::vector<int>> matrix;

    for (int x = 0; x < size*10; x++) {
        std::vector<int> temp_vector;
        for (int i = 0; i < size; i++) {
            temp_vector.push_back(dist(rd));
        }
        matrix.push_back(temp_vector);
    }

    return matrix;
}


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


std::string decrypt(matrix encrypted_matrix, std::vector<int> key, double add, int mod) {
    std::string solved_message;
    int message_len = encrypted_matrix.size();
    int dimension = key.size();

    for (int i = 0; i < message_len; i++) {
        int answer = 0;
        for (int x = 0; x < dimension; x++) {
            answer += encrypted_matrix[i][x] * key[x];
        }
        solved_message += (char)((add * round(((encrypted_matrix[i].back() - answer) % mod) / add)) / add);
    }

    return solved_message;
}


matrix encrypt(std::string message, matrix public_matrix, int mod, int add, int max_encryption_vectors) {
    int len = message.size();
    int dimension = public_matrix[0].size();
    std::uniform_int_distribution<int> pub_mat_index(0, public_matrix.size() - 1);
    std::uniform_int_distribution<int> num_encryption_vectors(2, max_encryption_vectors);
    matrix encrypted_message(len, std::vector<long long>(dimension));

    for (int i = 0; i < len; i++) {
        std::vector<long long> vector(dimension);
        for (int j = 0; j < num_encryption_vectors(rd); j++) {
            std::vector<long long> public_vector = public_matrix[pub_mat_index(rd)];
            for (int l = 0; l < dimension; l++) {
                vector[l] += public_vector[l];
            }
        }

        for (int k = 0; k < dimension; k++) {
            encrypted_message[i][k] += vector[k];
        }
        encrypted_message[i][dimension - 1] = (encrypted_message[i][dimension - 1] + ((int)message[i] * add)) % mod;
    }

    return encrypted_message;
}


std::vector<int> create_secret_key(int dimension) {
    std::uniform_int_distribution<int> dist(-8192, 8192);
    std::vector<int> key;

    for (int i = 0; i < dimension; i++) {
        key.push_back(dist(rd));
    }

    return key;
}


matrix create_public_key(std::vector<int> secret_key, int mod, int max_error) {
    int dimension = secret_key.size();
    std::uniform_int_distribution<int> dist(-8192, 8192);
    std::uniform_int_distribution<int> error(-max_error, max_error);
    std::vector<std::vector<long long>> public_key;

    for (int x = 0; x < dimension*10; x++) {
        std::vector<long long> temp_vector;
        long long answer = 0;
        for (int i = 0; i < dimension; i++) {
            int num = dist(rd);
            answer += (num * secret_key[i]);
            temp_vector.push_back(num);
        }
        temp_vector.push_back((answer + error(rd)) % mod);
        public_key.push_back(temp_vector);
    }

    return public_key;
}



PYBIND11_MODULE(lwe, handle) {
    handle.doc() = "LWE C++ Module";
    handle.def("decode", &decode);
    handle.def("encode", &encode);
    handle.def("decrypt", &decrypt);
    handle.def("encrypt", &encrypt);
    handle.def("create_secret", &create_secret_key);
    handle.def("create_public", &create_public_key);
}
