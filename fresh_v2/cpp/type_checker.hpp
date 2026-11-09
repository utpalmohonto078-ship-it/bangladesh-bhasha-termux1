#pragma once
#include <map>
#include <set>
#include <string>
#include <stdexcept>
#include <functional>
#include "parser.hpp"

namespace bb {

using Types = std::map<std::string, std::string>;
constexpr const char* UNKNOWN_TYPE = "unknown";

inline bool numeric_type(const std::string& t) {
    return t == "integer" || t == "float";
}

inline bool compatible_type(const std::string& a,
                            const std::string& b) {
    return a == UNKNOWN_TYPE || b == UNKNOWN_TYPE ||
           a == b || (a == "float" && b == "integer");
}


inline bool check_types(const NodeP& program) {
    Types globals;
    std::map<std::string, NodeP> functions;

    for (const auto& s : program->body)
        if (s->t == "Function") functions[s->name] = s;

    using FunctionKey =
        std::pair<std::string, std::vector<std::string>>;

    std::map<FunctionKey, std::string> fn_cache;
    std::set<FunctionKey> fn_active;
    std::vector<std::vector<std::string>> return_stack;

    std::function<std::string(const NodeP&, const Types&)> infer;
    std::function<void(const std::vector<NodeP>&, Types&,
                       const std::set<std::string>&)> check_body;
    std::function<std::string(const std::string&,
                              const std::vector<std::string>&)> check_function;

    auto merge_returns = [](const std::vector<std::string>& values) {
        if (values.empty()) return std::string(UNKNOWN_TYPE);

        std::set<std::string> unique(values.begin(), values.end());

        if (unique.count(UNKNOWN_TYPE))
            return std::string(UNKNOWN_TYPE);

        if (unique.size() == 1)
            return *unique.begin();

        bool all_numeric = true;
        for (const auto& t : unique)
            if (!numeric_type(t)) all_numeric = false;

        if (all_numeric) return std::string("float");
        return std::string(UNKNOWN_TYPE);
    };

    infer = [&](const NodeP& n, const Types& scope) -> std::string {
        if (!n) return UNKNOWN_TYPE;

        if (n->t == "Number")
            return n->is_float ? "float" : "integer";

        if (n->t == "String") return "string";
        if (n->t == "Boolean") return "boolean";

        if (n->t == "Variable") {
            auto i = scope.find(n->name);
            if (i != scope.end()) return i->second;

            i = globals.find(n->name);
            return i == globals.end() ? UNKNOWN_TYPE : i->second;
        }

        if (n->t == "Call") {
            std::vector<std::string> args;
            for (const auto& a : n->body)
                args.push_back(infer(a, scope));

            if (n->name == "ধরন" || n->name == "type_of")
                return "string";

            if (n->name == "দৈর্ঘ্য" || n->name == "length")
                return "integer";

            if (functions.count(n->name))
                return check_function(n->name, args);

            return UNKNOWN_TYPE;
        }

        if (n->t == "Unary") {
            auto v = infer(n->a, scope);

            if (v != UNKNOWN_TYPE && !numeric_type(v))
                throw std::runtime_error("Unary " + n->op +
                    ": numeric value required, got " + v);

            return v;
        }

        if (n->t == "Binary") {
            auto l = infer(n->a, scope);
            auto r = infer(n->b, scope);
            auto op = n->op;

            if (op == "+" || op == "-" || op == "*" ||
                op == "/" || op == "%") {

                if (op == "+" && l == "string" && r == "string")
                    return "string";

                if (l != UNKNOWN_TYPE && !numeric_type(l))
                    throw std::runtime_error("Operator " + op +
                        ": numeric value required, got " + l);

                if (r != UNKNOWN_TYPE && !numeric_type(r))
                    throw std::runtime_error("Operator " + op +
                        ": numeric value required, got " + r);

                if (l == UNKNOWN_TYPE || r == UNKNOWN_TYPE)
                    return UNKNOWN_TYPE;

                if (op == "/") return "float";

                return l == "float" || r == "float"
                    ? "float" : "integer";
            }

            if (op == "==" || op == "!=" || op == "<" ||
                op == ">" || op == "<=" || op == ">=") {

                if (l != UNKNOWN_TYPE && r != UNKNOWN_TYPE) {
                    bool nums = numeric_type(l) && numeric_type(r);

                    if (l != r && !nums)
                        throw std::runtime_error(
                            "Incompatible comparison: " + l + " and " + r);

                    if (op != "==" && op != "!=" &&
                        !(nums || (l == "string" && r == "string")))
                        throw std::runtime_error(
                            "Operator " + op +
                            ": values are not order-comparable");
                }

                return "boolean";
            }
        }

        throw std::runtime_error(
            "Static type checker: unsupported expression " + n->t);
    };

    check_body = [&](const std::vector<NodeP>& body, Types& scope,
                     const std::set<std::string>& dg) {

        for (const auto& s : body) {
            if (s->t == "Declare") {
                if (dg.count(s->name))
                    throw std::runtime_error(s->name +
                        ": cannot declare a GLOBAL variable locally");

                scope[s->name] = infer(s->a, scope);

            } else if (s->t == "Assign") {
                auto actual = infer(s->a, scope);

                auto i = dg.count(s->name)
                    ? globals.find(s->name) : globals.end();

                std::string expected = UNKNOWN_TYPE;

                if (i != globals.end()) {
                    expected = i->second;
                } else {
                    auto j = scope.find(s->name);
                    if (j != scope.end()) expected = j->second;
                }

                if (!compatible_type(expected, actual))
                    throw std::runtime_error(s->name +
                        ": cannot assign " + actual + " to " + expected);

            } else if (s->t == "Print") {
                infer(s->a, scope);

            } else if (s->t == "If") {
                auto t = infer(s->a, scope);

                if (t != "boolean" && t != UNKNOWN_TYPE)
                    throw std::runtime_error(
                        "IF condition must be Boolean, got " + t);

                check_body(s->body, scope, dg);
                check_body(s->otherwise, scope, dg);

            } else if (s->t == "While") {
                auto t = infer(s->a, scope);

                if (t != "boolean" && t != UNKNOWN_TYPE)
                    throw std::runtime_error(
                        "WHILE condition must be Boolean, got " + t);

                check_body(s->body, scope, dg);

            } else if (s->t == "Repeat") {
                auto t = infer(s->a, scope);

                if (!numeric_type(t) && t != UNKNOWN_TYPE)
                    throw std::runtime_error(
                        "REPEAT count must be numeric, got " + t);

                check_body(s->body, scope, dg);

            } else if (s->t == "Return") {
                auto t = infer(s->a, scope);

                if (!return_stack.empty())
                    return_stack.back().push_back(t);

            } else if (s->t == "Global") {
                // GLOBAL declarations are collected before checking.
            }
        }
    };

    check_function = [&](const std::string& name,
                         const std::vector<std::string>& arg_types)
                         -> std::string {

        auto fi = functions.find(name);
        if (fi == functions.end()) return UNKNOWN_TYPE;

        const auto& fn = fi->second;

        if (fn->params.size() != arg_types.size())
            throw std::runtime_error(
                name + ": wrong argument count");

        FunctionKey key{name, arg_types};

        auto cached = fn_cache.find(key);
        if (cached != fn_cache.end()) return cached->second;

        // Recursive cycle: conservatively return UNKNOWN.
        if (fn_active.count(key)) return UNKNOWN_TYPE;

        fn_active.insert(key);
        return_stack.emplace_back();

        try {
            Types scope;

            for (size_t i = 0; i < fn->params.size(); ++i)
                scope[fn->params[i]] = arg_types[i];

            std::set<std::string> dg;

            std::function<void(const std::vector<NodeP>&)> collect;
            collect = [&](const std::vector<NodeP>& body) {
                for (const auto& s : body) {
                    if (s->t == "Global") {
                        dg.insert(s->name);
                    } else if (s->t == "If") {
                        collect(s->body);
                        collect(s->otherwise);
                    } else if (s->t == "Repeat" || s->t == "While") {
                        collect(s->body);
                    }
                }
            };

            collect(fn->body);
            check_body(fn->body, scope, dg);

            auto result = merge_returns(return_stack.back());

            return_stack.pop_back();
            fn_active.erase(key);
            fn_cache[key] = result;

            return result;

        } catch (...) {
            return_stack.pop_back();
            fn_active.erase(key);
            throw;
        }
    };

    // Infer global declarations in source order.
    for (const auto& s : program->body)
        if (s->t == "Declare")
            globals[s->name] = infer(s->a, globals);

    // Check each function using unknown parameter types.
    for (const auto& entry : functions) {
        std::vector<std::string> args(
            entry.second->params.size(), UNKNOWN_TYPE);
        check_function(entry.first, args);
    }

    // Check top-level executable statements.
    Types scope = globals;

    for (const auto& s : program->body)
        if (s->t != "Declare" && s->t != "Function")
            check_body({s}, scope, {});

    return true;
}

} // namespace bb
