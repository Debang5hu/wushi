// Utility to get a query parameter by name from the URL
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

// Display the error message if present and remove it from the URL
function displayAndTrimError() {
    const errorMessage = getQueryParam('error');

    if (errorMessage) {
        const errorElement = document.getElementById('error-msg');
        if (errorElement) {
            errorElement.textContent = decodeURIComponent(errorMessage);
            errorElement.style.display = 'block';
        }

        // Remove the error query parameter from the URL
        const url = new URL(window.location.href);
        url.searchParams.delete('error');
        window.history.replaceState({}, document.title, url.pathname);
    }
}

// Generate a simple math problem (addition or subtraction) and return the correct answer
function generateMathProblem() {
    const num1 = Math.floor(Math.random() * 10) + 1;
    const num2 = Math.floor(Math.random() * 10) + 1;
    const isAddition = Math.random() < 0.5; // Randomly choose addition or subtraction

    const problemLabel = document.getElementById('math-problem');
    const operator = isAddition ? '+' : '-';
    const answer = isAddition ? num1 + num2 : num1 - num2;

    if (problemLabel) {
        problemLabel.textContent = `${num1} ${operator} ${num2} = ?`;
    }

    return answer;
}

// Validate the CAPTCHA input before allowing form submission
function validateCaptcha() {
    const userCaptcha = document.getElementById('captcha').value;
    const expectedCaptcha = document.getElementById('captcha_answer').value;

    if (parseInt(userCaptcha, 10) !== parseInt(expectedCaptcha, 10)) {
        alert("Incorrect CAPTCHA. Please try again.");
        return false;
    }

    return true;
}

// Initialize the page on load
window.addEventListener('DOMContentLoaded', () => {
    displayAndTrimError();

    // Generate the math problem and store the correct answer
    const captchaAnswer = generateMathProblem();
    const captchaInput = document.getElementById('captcha_answer');

    if (captchaInput) {
        captchaInput.value = captchaAnswer;
    }
});
