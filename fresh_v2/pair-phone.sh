#!/data/data/com.termux/files/usr/bin/bash

IP="192.168.10.57"

echo "================================"
echo " BANGLADESH BHASHA - ADB PAIR"
echo "================================"
echo
echo "ফোনে Wireless Debugging চালু রাখুন।"
echo "Pair device with pairing code খুলুন।"
echo

read -r -p "শুধু Pairing Port লিখুন: " PORT

if ! [[ "$PORT" =~ ^[0-9]{1,5}$ ]] || (( PORT < 1 || PORT > 65535 )); then
    echo "ভুল Port! আবার চেষ্টা করুন।"
    exit 1
fi

adb start-server

echo
echo "এখন ফোনের ৬ সংখ্যার Wi-Fi Pairing Code চাইবে।"
echo "শুধু নতুন কোডটি একবার লিখুন।"
echo

adb pair "$IP:$PORT"

echo
echo "Pairing প্রক্রিয়া শেষ।"
