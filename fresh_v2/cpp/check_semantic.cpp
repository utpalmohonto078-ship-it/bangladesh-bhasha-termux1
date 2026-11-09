#include <iostream>
#include <sstream>
#include <string>
#include "lexer.hpp"
#include "semantic.hpp"

int main() {
    std::ostringstream input;
    input << std::cin.rdbuf();

    try {
        auto tokens = bb::tokenize(input.str());
        auto ast = bb::parse(tokens);
        bb::analyze(ast);
        std::cout << "SEMANTIC_OK\n";
        return 0;
    } catch (const std::exception& e) {
        std::cout << "SEMANTIC_ERROR: " << e.what() << "\n";
        return 1;
    }
}
