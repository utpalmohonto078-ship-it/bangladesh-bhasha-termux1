#!/data/data/com.termux/files/usr/bin/bash
cd ~/BANGLADESH-BHASHA-ULTIMATE/fresh_v2
D=cpp/cases/scope; mkdir -p $D
printf 'সংখ্যা x = 1\nফাংশন f()\n  সংখ্যা x = "a"\n  ফেরত x\nশেষ\nদেখাও f()\n' > $D/c01_shadow_local.bb
printf 'সংখ্যা i = 0\nযতক্ষণ i < 2\n  সংখ্যা k = 5\n  i = i + 1\nশেষ\nদেখাও k\n' > $D/c02_loop_decl_visible.bb
printf 'ফাংশন f(a)\n  যদি সত্য\n    সংখ্যা t = 1\n  শেষ\n  যদি সত্য\n    সংখ্যা t = 2\n  শেষ\nশেষ\n' > $D/c03_dup_in_branches.bb
printf 'ফাংশন f(a)\n  সংখ্যা a = 1\n  ফেরত a\nশেষ\n' > $D/c04_param_redeclare.bb
printf 'সংখ্যা x = 1\nx = "s"\n' > $D/c05_retype_top.bb
printf 'সংখ্যা x = 1\nx = 2.5\n' > $D/c06_int_to_float.bb
printf 'সংখ্যা y = 1.5\ny = 2\n' > $D/c07_float_accepts_int.bb
printf 'সংখ্যা g = 1\nফাংশন f()\n  g = 2\nশেষ\nদেখাও f()\n' > $D/c08_assign_global_no_decl.bb
printf 'দেখাও z\nসংখ্যা z = 1\n' > $D/c09_use_before_decl.bb
printf 'সংখ্যা a = b\nসংখ্যা b = 1\n' > $D/c10_init_forward_ref.bb
printf 'ফাংশন f(a)\n  a = "x"\n  ফেরত a\nশেষ\nদেখাও f(1)\n' > $D/c11_param_retype.bb

norm() { if [ "$2" -eq 0 ]; then echo OK; else
  echo "ERR|$(echo "$1" | head -1 | sed -e 's/^SEMANTIC_ERROR: //' -e 's/^Error: //')"; fi; }
pass=0; fail=0
for f in $D/*.bb; do
  po=$(./bhasha check "$f" 2>&1); pr=$?
  co=$(./cpp/check_semantic < "$f" 2>&1); cr=$?
  jo=$(node js/check_semantic.js < "$f" 2>&1); jr=$?
  P=$(norm "$po" $pr); C=$(norm "$co" $cr); J=$(norm "$jo" $jr)
  if [ "$P" = "$C" ] && [ "$P" = "$J" ]; then
    pass=$((pass+1)); echo "মিল   $(basename $f): ${P:0:60}"
  else
    fail=$((fail+1)); echo "অমিল  $(basename $f)"
    echo "   Python: $P"; echo "   C++:    $C"; echo "   JS:     $J"
  fi
done
echo "== পাস $pass / ফেল $fail =="
[ $fail -eq 0 ] && git add -A && git commit -qm "scope and variable parity tests (3-way)" && echo "কমিট হয়েছে"
