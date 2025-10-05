# [adimicoli.github.io](https://mars2380.github.io/)

```bash
npm install -g create-react-app
create-react-app jobserve-app --template typescript
npm install
cd jobserve-app
npm install --save bootstrap
npm start
```

```bash
cd typescript
npm install typescript --save-dev
npx tsc
npx tsc --init
cp tsconfig.json tsconfig.json.bak

cat <<EOF > tsconfig.json
{
  "include": ["src"],
  "compilerOptions": {
    "outDir": "./build"
  }
}
EOF

tsc src/script.ts && node src/script.js
```