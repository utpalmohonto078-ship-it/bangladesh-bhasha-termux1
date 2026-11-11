#!/data/data/com.termux/files/usr/bin/bash
cd ~/BANGLADESH-BHASHA-ULTIMATE/fresh_v2
H=cpp/type_checker.hpp
BK=$H.bak_prefix_$(date +%H%M%S)
cp $H $BK
python3 - <<'PY'
p="cpp/type_checker.hpp"
s=open(p,encoding="utf-8").read()
old="""        } catch (...) {
            return_stack.pop_back();
            fn_active.erase(key);
            throw;
        }"""
new="""        } catch (const std::exception& e) {
            return_stack.pop_back();
            fn_active.erase(key);
            std::string sig = name + "(";
            for (size_t i = 0; i < arg_types.size(); ++i) {
                if (i) sig += ", ";
                sig += arg_types[i];
            }
            sig += "): ";
            throw std::runtime_error(sig + e.what());
        } catch (...) {
            return_stack.pop_back();
            fn_active.erase(key);
            throw;
        }"""
if s.count(old)!=1:
    print("PATCH_SKIP: প্যাটার্ন ঠিক ১ বার পাওয়া যায়নি, ফাইল অপরিবর্তিত"); raise SystemExit(2)
open(p,"w",encoding="utf-8").write(s.replace(old,new))
print("PATCH_OK")
PY
[ $? -ne 0 ] && { cp $BK $H; exit 1; }
g++ -std=c++17 -O1 cpp/check_semantic.cpp -Icpp -o cpp/check_semantic 2>build_err.txt || {
  echo "বিল্ড ফেল, রিস্টোর"; cp $BK $H; head -20 build_err.txt; exit 1; }
D=cpp/cases/infer2; mkdir -p $D
cat > $D/n1_nested_global.bb <<'BB'
সংখ্যা total = 0
ফাংশন f(n)
  পুনরাবৃত্তি 2
    যতক্ষণ n > 0
      যদি n > 1
        গ্লোবাল total
        total = total + n
      শেষ
      n = n - 1
    শেষ
  শেষ
  ফেরত total
শেষ
দেখাও f(3)
BB
cat > $D/n2_global_type.bb <<'BB'
সংখ্যা total = 0
ফাংশন f(n)
  গ্লোবাল total
  total = "x"
  ফেরত total
শেষ
দেখাও f(1)
BB
cat > $D/n3_recur_merge.bb <<'BB'
ফাংশন g(n)
  যদি n < 1
    ফেরত 0
  নাহলে
    ফেরত g(n - 1) + 0.5
  শেষ
শেষ
দেখাও g(3)
BB
cat > $D/n4_nested_call_err.bb <<'BB'
ফাংশন inner(a)
  ফেরত a + 1
শেষ
ফাংশন outer(b)
  ফেরত inner(b)
শেষ
দেখাও outer("x")
BB
cat > $D/n5_while_cond.bb <<'BB'
ফাংশন h(s)
  যতক্ষণ s
    ফেরত 1
  শেষ
  ফেরত 0
শেষ
দেখাও h("x")
BB
pass=0; fail=0
for f in $D/*.bb cpp/cases/infer/t5_argtype.bb; do
  cout=$(./cpp/check_semantic < $f 2>&1); crc=$?
  pout=$(./bhasha check $f 2>&1); prc=$?
  if [ $crc -eq 0 ] && [ $prc -eq 0 ]; then
    pass=$((pass+1)); echo "মিল   $(basename $f): OK"; continue; fi
  cm=$(echo "$cout" | head -1 | sed 's/^SEMANTIC_ERROR: //')
  pm=$(echo "$pout" | head -1 | sed 's/^Error: //')
  if [ $crc -ne 0 ] && [ $prc -ne 0 ] && [ "$cm" = "$pm" ]; then
    pass=$((pass+1)); echo "মিল   $(basename $f): ERR | $cm"
  else
    fail=$((fail+1)); echo "অমিল  $(basename $f): C++rc=$crc Pyrc=$prc"
    echo "   C++:    $cout"; echo "   Python: $pout"
  fi
done
echo "== পাস $pass / ফেল $fail =="
echo "ব্যাকআপ: $BK"
