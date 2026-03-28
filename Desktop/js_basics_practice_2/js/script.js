// ==========================================
// Практична робота 2 - Варіант 1
// ==========================================

/**
 * Task 1: FizzBuzz Classic [cite: 600-603]
 * Оцінює числа від 1 до n і повертає масив рядків за правилами FizzBuzz.
 * @param {number} n - Верхня межа числового діапазону
 * @returns {string[]} Масив результатів
 */
const fizzBuzz = (n) => {
    if (typeof n !== 'number' || n <= 0 || !Number.isInteger(n)) return [];
    
    const result = [];
    for (let i = 1; i <= n; i++) {
        if (i % 15 === 0) result.push("FizzBuzz");
        else if (i % 3 === 0) result.push("Fizz");
        else if (i % 5 === 0) result.push("Buzz");
        else result.push(i.toString());
    }
    return result;
};

/**
 * Task 2: Number Sign [cite: 604-607]
 * Визначає знак числа, обробляючи крайні випадки.
 * @param {number} num - Число для перевірки
 * @returns {number|NaN} 1 (позитивне), -1 (негативне), 0 (нуль) або NaN
 */
const getNumberSign = (num) => {
    if (Number.isNaN(num)) return NaN;
    if (num === 0) return 0; // Обробляє як 0, так і -0
    if (num > 0) return 1;   // Обробляє додатні числа та Infinity
    if (num < 0) return -1;  // Обробляє від'ємні числа та -Infinity
    return NaN;
};

/**
 * Task 3: Leap Year Checker [cite: 608-612]
 * Перевіряє, чи є рік високосним.
 * @param {number} year - Рік для перевірки
 * @returns {boolean} Результат перевірки
 */
const isLeapYear = (year) => {
    if (typeof year !== 'number' || !Number.isInteger(year) || year <= 0) return false;
    return (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
};

/**
 * Task 4: Triangle Type Classifier [cite: 613-616]
 * Визначає тип трикутника за його сторонами.
 * @param {number} a - Перша сторона
 * @param {number} b - Друга сторона
 * @param {number} c - Третя сторона
 * @returns {string} Тип трикутника ("equilateral", "isosceles", "scalene", "invalid")
 */
const getTriangleType = (a, b, c) => {
    // Валідація сторін і перевірка правила існування трикутника
    if (a <= 0 || b <= 0 || c <= 0) return "invalid";
    if (a + b <= c || a + c <= b || b + c <= a) return "invalid";

    if (a === b && b === c) return "equilateral";
    if (a === b || a === c || b === c) return "isosceles";
    return "scalene";
};

/**
 * Task 5: Grade Letter Calculator [cite: 617-621]
 * Перетворює числову оцінку на літерну з модифікаторами + або -.
 * @param {number} score - Оцінка від 0 до 100
 * @returns {string} Літерна оцінка (наприклад, "B+", "C-", "F")
 */
const calculateGradeLetter = (score) => {
    if (typeof score !== 'number' || score < 0 || score > 100) return "Invalid";
    if (score < 60) return "F";
    if (score === 100) return "A+";

    let letter = "";
    if (score >= 90) letter = "A";
    else if (score >= 80) letter = "B";
    else if (score >= 70) letter = "C";
    else if (score >= 60) letter = "D";

    const lastDigit = score % 10;
    let modifier = "";
    // Для верхніх 3 балів (7, 8, 9) даємо +, для нижніх 3 балів (0, 1, 2) даємо -
    if (lastDigit >= 7) modifier = "+";
    else if (lastDigit <= 2) modifier = "-";

    return letter + modifier;
};

// ==========================================
// UNIT TESTS (Виведення результатів у консоль)
// ==========================================
console.log("%c=== ЗАПУСК UNIT ТЕСТІВ ===", "color: blue; font-weight: bold; font-size: 14px;");

const runTest = (testName, condition) => {
    if (condition) {
        console.log(`✅ ${testName} - PASSED`);
    } else {
        console.error(`❌ ${testName} - FAILED`);
    }
};

// 1. Tests for FizzBuzz
console.log("\n--- Testing FizzBuzz ---");
runTest("FizzBuzz(15) length is 15", fizzBuzz(15).length === 15);
runTest("FizzBuzz(15) last element is 'FizzBuzz'", fizzBuzz(15)[14] === "FizzBuzz");
runTest("FizzBuzz(5) handles Buzz", fizzBuzz(5)[4] === "Buzz");
runTest("FizzBuzz(-5) returns empty array (Edge Case)", fizzBuzz(-5).length === 0);

// 2. Tests for Number Sign
console.log("\n--- Testing Number Sign ---");
runTest("Sign of 42 is 1", getNumberSign(42) === 1);
runTest("Sign of -15 is -1", getNumberSign(-15) === -1);
runTest("Sign of 0 is 0", getNumberSign(0) === 0);
runTest("Sign of -0 is 0 (Edge Case)", getNumberSign(-0) === 0);
runTest("Sign of Infinity is 1 (Edge Case)", getNumberSign(Infinity) === 1);
runTest("Sign of NaN is NaN (Edge Case)", Number.isNaN(getNumberSign(NaN)));

// 3. Tests for Leap Year
console.log("\n--- Testing Leap Year ---");
runTest("2024 is Leap Year", isLeapYear(2024) === true);
runTest("2000 is Leap Year (Edge Case)", isLeapYear(2000) === true);
runTest("1900 is NOT Leap Year (Edge Case)", isLeapYear(1900) === false);
runTest("2023 is NOT Leap Year", isLeapYear(2023) === false);

// 4. Tests for Triangle Classifier
console.log("\n--- Testing Triangle Classifier ---");
runTest("3, 3, 3 is equilateral", getTriangleType(3, 3, 3) === "equilateral");
runTest("3, 4, 4 is isosceles", getTriangleType(3, 4, 4) === "isosceles");
runTest("3, 4, 5 is scalene", getTriangleType(3, 4, 5) === "scalene");
runTest("1, 2, 10 is invalid (Validation)", getTriangleType(1, 2, 10) === "invalid");
runTest("-1, 5, 5 is invalid (Edge Case)", getTriangleType(-1, 5, 5) === "invalid");

// 5. Tests for Grade Letter
console.log("\n--- Testing Grade Calculator ---");
runTest("Score 100 is A+", calculateGradeLetter(100) === "A+");
runTest("Score 88 is B+", calculateGradeLetter(88) === "B+");
runTest("Score 75 is C", calculateGradeLetter(75) === "C");
runTest("Score 61 is D-", calculateGradeLetter(61) === "D-");
runTest("Score 59 is F", calculateGradeLetter(59) === "F");
runTest("Score 105 is Invalid (Edge Case)", calculateGradeLetter(105) === "Invalid");