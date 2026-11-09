#pragma once
#include <map>
#include <set>
#include <string>
#include <stdexcept>
#include <functional>
#include <vector>
#include "parser.hpp"
#include "type_checker.hpp"

namespace bb {

inline bool analyze(const NodeP& program) {
    std::set<std::string> top_globals;
    std::map<std::string, NodeP> functions;

    // Collect top-level declarations and functions.
    for (const auto& s : program->body) {
        if (s->t == "Declare") {
            if (!top_globals.insert(s->name).second)
                throw std::runtime_error("Duplicate variable: " + s->name);
        }
        if (s->t == "Function") {
            if (functions.count(s->name))
                throw std::runtime_error("Duplicate function: " + s->name);
            functions[s->name] = s;
        }
    }

    // Collect GLOBAL declarations recursively.
    std::function<void(const std::vector<NodeP>&,
                       std::set<std::string>&)> collect_globals;

    collect_globals = [&](const std::vector<NodeP>& body,
                          std::set<std::string>& result) {
        for (const auto& s : body) {
            if (s->t == "Global") result.insert(s->name);
            else if (s->t == "If") {
                collect_globals(s->body, result);
                collect_globals(s->otherwise, result);
            } else if (s->t == "Repeat" || s->t == "While") {
                collect_globals(s->body, result);
            }
        }
    };

    // Collect local declarations recursively.
    std::function<void(const std::vector<NodeP>&,
                       std::set<std::string>&)> collect_locals;

    collect_locals = [&](const std::vector<NodeP>& body,
                         std::set<std::string>& result) {
        for (const auto& s : body) {
            if (s->t == "Declare") result.insert(s->name);
            else if (s->t == "If") {
                collect_locals(s->body, result);
                collect_locals(s->otherwise, result);
            } else if (s->t == "Repeat" || s->t == "While") {
                collect_locals(s->body, result);
            }
        }
    };

    std::function<void(const NodeP&, const std::set<std::string>&,
                       bool, const std::set<std::string>&)> expression;

    expression = [&](const NodeP& n,
                     const std::set<std::string>& scope,
                     bool init_mode,
                     const std::set<std::string>& initialized) {
        if (!n) return;

        if (n->t == "Number" || n->t == "String" ||
            n->t == "Boolean") return;

        if (n->t == "Variable") {
            if (init_mode) {
                if (!initialized.count(n->name))
                    throw std::runtime_error(
                        "Undefined variable: " + n->name);
            } else if (!scope.count(n->name) &&
                       !top_globals.count(n->name)) {
                throw std::runtime_error(
                    "Undefined variable: " + n->name);
            }
            return;
        }

        if (n->t == "Call") {
            int expected = -1;
            auto f = functions.find(n->name);

            if (f != functions.end())
                expected = static_cast<int>(f->second->params.size());
            else if (n->name == "ধরন" || n->name == "type_of" ||
                     n->name == "দৈর্ঘ্য" || n->name == "length")
                expected = 1;
            else
                throw std::runtime_error(
                    "Unknown function: " + n->name);

            int actual = static_cast<int>(n->body.size());
            if (actual != expected)
                throw std::runtime_error(
                    n->name + ": expected " + std::to_string(expected) +
                    " arguments, got " + std::to_string(actual));

            for (const auto& a : n->body)
                expression(a, scope, init_mode, initialized);
            return;
        }

        if (n->t == "Binary") {
            expression(n->a, scope, init_mode, initialized);
            expression(n->b, scope, init_mode, initialized);
            return;
        }

        if (n->t == "Unary") {
            expression(n->a, scope, init_mode, initialized);
            return;
        }

        throw std::runtime_error("Unsupported expression: " + n->t);
    };

    std::function<void(const std::vector<NodeP>&,
                       std::set<std::string>&, bool,
                       const std::set<std::string>&, int)> statements;

    statements = [&](const std::vector<NodeP>& body,
                     std::set<std::string>& scope,
                     bool in_function,
                     const std::set<std::string>& declared_globals,
                     int loop_depth) {
        for (const auto& s : body) {
            if (s->t == "Declare") {
                if (scope.count(s->name))
                    throw std::runtime_error(
                        "Duplicate local variable: " + s->name);
                if (declared_globals.count(s->name))
                    throw std::runtime_error(
                        s->name + " is declared GLOBAL");

                expression(s->a, scope, false, {});
                scope.insert(s->name);
            }
            else if (s->t == "Assign") {
                if (!scope.count(s->name) &&
                    !declared_globals.count(s->name) &&
                    (in_function || !top_globals.count(s->name))) {
                    throw std::runtime_error(
                        "Assignment to undeclared variable: " + s->name);
                }
                expression(s->a, scope, false, {});
            }
            else if (s->t == "Print") {
                expression(s->a, scope, false, {});
            }
            else if (s->t == "If") {
                expression(s->a, scope, false, {});
                statements(s->body, scope, in_function,
                           declared_globals, loop_depth);
                statements(s->otherwise, scope, in_function,
                           declared_globals, loop_depth);
            }
            else if (s->t == "Repeat" || s->t == "While") {
                expression(s->a, scope, false, {});
                statements(s->body, scope, in_function,
                           declared_globals, loop_depth + 1);
            }
            else if (s->t == "Break") {
                if (loop_depth == 0)
                    throw std::runtime_error("BREAK outside loop");
            }
            else if (s->t == "Continue") {
                if (loop_depth == 0)
                    throw std::runtime_error("CONTINUE outside loop");
            }
            else if (s->t == "Return") {
                if (!in_function)
                    throw std::runtime_error("RETURN outside function");
                expression(s->a, scope, false, {});
            }
            else if (s->t == "Global") {
                if (!in_function)
                    throw std::runtime_error("GLOBAL outside function");
                if (!top_globals.count(s->name))
                    throw std::runtime_error(
                        "Unknown global variable: " + s->name);
            }
        }
    };

    // Validate function bodies.
    for (const auto& entry : functions) {
        const auto& fn = entry.second;
        std::set<std::string> declared_globals;
        collect_globals(fn->body, declared_globals);

        std::set<std::string> locals;
        for (const auto& p : fn->params) {
            if (!locals.insert(p).second)
                throw std::runtime_error(
                    "Duplicate parameter: " + p);
        }
        collect_locals(fn->body, locals);

        for (const auto& g : declared_globals) {
            if (std::find(fn->params.begin(), fn->params.end(), g)
                != fn->params.end())
                throw std::runtime_error(
                    "GLOBAL cannot conflict with a parameter");
            if (locals.count(g))
                throw std::runtime_error(
                    "GLOBAL cannot conflict with a local variable");
        }

        std::set<std::string> scope;
        for (const auto& p : fn->params) scope.insert(p);

        statements(fn->body, scope, true, declared_globals, 0);
    }

    // Validate top-level executable statements.
    for (const auto& s : program->body) {
        if (s->t == "Declare" || s->t == "Function") continue;
        std::set<std::string> empty_scope;
        statements({s}, empty_scope, false, {}, 0);
    }

    // Validate global initializers in declaration order.
    std::set<std::string> initialized;
    for (const auto& s : program->body) {
        if (s->t != "Declare") continue;
        expression(s->a, {}, true, initialized);
        initialized.insert(s->name);
    }

    // Run static type checking after semantic validation.
    return check_types(program);
}

} // namespace bb
