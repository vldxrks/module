// ==========================================
// Практична робота 3 - Варіант 1 (Array Processing)
// ==========================================

/**
 * Task 1: Maximum Subarray Sum (Kadane's Algorithm)
 * Знаходить максимальну суму безперервного підмасиву.
 * @param {number[]} nums - Масив чисел
 * @returns {number} Максимальна сума
 */
const maxSubArray = (nums) => {
    if (!Array.isArray(nums) || nums.length === 0) return 0;
    
    let currentSum = nums[0];
    let maxSum = nums[0];
    
    for (let i = 1; i < nums.length; i++) {
        currentSum = Math.max(nums[i], currentSum + nums[i]);
        maxSum = Math.max(maxSum, currentSum);
    }
    
    return maxSum;
};

/**
 * Task 2: Rotate Array
 * Зсуває масив вправо на k кроків (in-place).
 * @param {number[]} nums - Масив для зсуву
 * @param {number} k - Кількість кроків
 * @returns {number[]} Змінений масив
 */
const rotateArray = (nums, k) => {
    if (!Array.isArray(nums) || nums.length === 0) return nums;
    
    k = k % nums.length; // Якщо k більше за довжину масиву
    if (k === 0) return nums;

    // Допоміжна функція для реверсу частини масиву
    const reverse = (arr, start, end) => {
        while (start < end) {
            [arr[start], arr[end]] = [arr[end], arr[start]]; // Swap
            start++;
            end--;
        }
    };

    reverse(nums, 0, nums.length - 1); // Реверс всього масиву
    reverse(nums, 0, k - 1);           // Реверс перших k елементів
    reverse(nums, k, nums.length - 1); // Реверс решти

    return nums;
};

/**
 * Task 3: Move Zeroes
 * Переміщує всі нулі в кінець масиву, зберігаючи порядок інших елементів (in-place).
 * @param {number[]} nums - Масив чисел
 * @returns {number[]} Змінений масив
 */
const moveZeroes = (nums) => {
    if (!Array.isArray(nums)) return [];
    
    let lastNonZeroFoundAt = 0;
    
    for (let i = 0; i < nums.length; i++) {
        if (nums[i] !== 0) {
            // Swap
            [nums[lastNonZeroFoundAt], nums[i]] = [nums[i], nums[lastNonZeroFoundAt]];
            lastNonZeroFoundAt++;
        }
    }
    
    return nums;
};

/**
 * Task 4: Two Sum II - Input Array Is Sorted
 * Знаходить індекси двох чисел, сума яких дорівнює target (Two Pointers).
 * @param {number[]} numbers - Відсортований масив
 * @param {number} target - Цільова сума
 * @returns {number[]} Масив з двома індексами
 */
const twoSumSorted = (numbers, target) => {
    if (!Array.isArray(numbers) || numbers.length < 2) return [];
    
    let left = 0;
    let right = numbers.length - 1;
    
    while (left < right) {
        const sum = numbers[left] + numbers[right];
        
        if (sum === target) return [left, right];
        else if (sum < target) left++;
        else right--;
    }
    
    return [];
};

/**
 * Task 5: Container With Most Water
 * Знаходить дві лінії, які разом з віссю X утворюють контейнер, що містить найбільше води.
 * @param {number[]} heights - Масив висот
 * @returns {number} Максимальна площа води
 */
const maxArea = (heights) => {
    if (!Array.isArray(heights) || heights.length < 2) return 0;
    
    let maxWater = 0;
    let left = 0;
    let right = heights.length - 1;
    
    while (left < right) {
        const width = right - left;
        const minHeight = Math.min(heights[left], heights[right]);
        maxWater = Math.max(maxWater, width * minHeight);
        
        // Рухаємо менший вказівник
        if (heights[left] < heights[right]) left++;
        else right--;
    }
    
    return maxWater;
};

// ==========================================
// UNIT TESTS
// ==========================================
console.log("%c=== ЗАПУСК UNIT ТЕСТІВ (Цикли та Масиви) ===", "color: #27ae60; font-weight: bold; font-size: 14px;");

const runTest = (testName, condition) => {
    if (condition) console.log(`✅ ${testName} - PASSED`);
    else console.error(`❌ ${testName} - FAILED`);
};

// 1. Tests for Kadane's
console.log("\n--- Maximum Subarray Sum ---");
runTest("Normal array [-2,1,-3,4,-1,2,1,-5,4] -> 6", maxSubArray([-2,1,-3,4,-1,2,1,-5,4]) === 6);
runTest("All negative [-5,-2,-9] -> -2", maxSubArray([-5,-2,-9]) === -2);
runTest("Empty array -> 0 (Edge Case)", maxSubArray([]) === 0);

// 2. Tests for Rotate Array
console.log("\n--- Rotate Array ---");
const arr1 = [1,2,3,4,5,6,7];
runTest("Rotate by 3", rotateArray(arr1, 3).join() === "5,6,7,1,2,3,4");
const arr2 = [-1,-100,3,99];
runTest("Rotate by 2", rotateArray(arr2, 2).join() === "3,99,-1,-100");

// 3. Tests for Move Zeroes
console.log("\n--- Move Zeroes ---");
runTest("[0,1,0,3,12] -> [1,3,12,0,0]", moveZeroes([0,1,0,3,12]).join() === "1,3,12,0,0");
runTest("No zeroes [1,2,3] -> [1,2,3]", moveZeroes([1,2,3]).join() === "1,2,3");

// 4. Tests for Two Sum Sorted
console.log("\n--- Two Sum (Sorted) ---");
runTest("[2,7,11,15], target 9 -> [0,1]", twoSumSorted([2,7,11,15], 9).join() === "0,1");
runTest("Target not found -> []", twoSumSorted([2,7,11,15], 100).length === 0);

// 5. Tests for Container With Most Water
console.log("\n--- Container With Most Water ---");
runTest("[1,8,6,2,5,4,8,3,7] -> 49", maxArea([1,8,6,2,5,4,8,3,7]) === 49);
runTest("[1,1] -> 1", maxArea([1,1]) === 1);