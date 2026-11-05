# পাঠ ০৪: Static Type System

প্রোগ্রাম চালানোর আগেই Compiler যখন ভেরিয়েবল ও Expression-এর ধরন যাচাই করে, তাকে Static Type Checking বলে।

## সমর্থিত ধরন
- integer: পূর্ণসংখ্যা
- float: দশমিক সংখ্যা
- string: টেক্সট
- boolean: সত্য অথবা মিথ্যা
- unknown: অনির্ধারিত ধরন

## উদাহরণ
```bb
সংখ্যা x = 5
দেখাও x + 2.5
```

ফলাফল: `7.5`

## সীমাবদ্ধতা
- Function parameter-এর নির্দিষ্ট Type এখনো নেই।
- Function return type-এর পূর্ণ যাচাই এখনো নেই।
