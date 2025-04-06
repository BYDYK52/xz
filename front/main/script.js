
let a = 0
a++
// + или -- прибавляет или отнимает единицу
console.log(a)
console.log(String(a))
// пример преобразования числа в строку, также можно сделать с Number и Boolean НО с number можно сделать +

console.log(
    +'134'
)
// тоби ж я из строки сделал число

// 0 NaN null undefined '' - это все false, остальное - это все true

let sms = 'ку ку'
console.log(sms)
sms += 'салам алейкум'
console.log(sms)

// вот как добавить что то в строку Которая уже есть

const sms2 = prompt('ку ку','ку')
if (sms2 === ''){
console.log('Ну и ладно')
}
else{
    console.log(`Ответ на сообщение : ${sms2}`)
}
const sms3 = confirm(sms2)
if (sms3 === true){
console.log('ты нажал ок')
}
else{
    console.log('ты нажал отмена')
}
// пример как сделать всплывающие окно с вопросом полем для ввода ответа
// и проверкой введенного ответа