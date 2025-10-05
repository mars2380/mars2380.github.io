let firstName: string = "Dylan";
console.log(firstName);

const json = JSON.parse("55");
console.log(typeof json);
console.log(json);


function printStatusCode(code: string | number) {
  console.log(`My status code is ${code}.`)
}
printStatusCode(404);
printStatusCode('404');

function getTime(): number {
  return new Date().getTime();
}
console.log(getTime());

function printHello(): void {
  console.log('Hello!');
}
printHello();

function multiply(a: number, b: number) {
  return a * b;
}
console.log(multiply(4,5))

// the `?` operator here marks parameter `c` as optional
function add(a: number, b: number, c?: number) {
  return a + b + (c || 0);
}
console.log(add(2,3,5))