var firstName = "Dylan";
console.log(firstName);
var json = JSON.parse("55");
console.log(typeof json);
console.log(json);
function printStatusCode(code) {
    console.log("My status code is ".concat(code, "."));
}
printStatusCode(404);
printStatusCode('404');
function getTime() {
    return new Date().getTime();
}
console.log(getTime());
function printHello() {
    console.log('Hello!');
}
printHello();
function multiply(a, b) {
    return a * b;
}
console.log(multiply(4, 5));
// the `?` operator here marks parameter `c` as optional
function add(a, b, c) {
    return a + b + (c || 0);
}
console.log(add(2, 3, 5));
