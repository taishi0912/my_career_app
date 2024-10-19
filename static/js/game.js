document.addEventListener('DOMContentLoaded', function () {
    const choiceButtons = document.querySelectorAll('.choice-button');
    const goBackButton = document.getElementById('go-back-button');
    const timeCrystalsDisplay = document.getElementById('time-crystals');

    choiceButtons.forEach(button => {
        button.addEventListener('click', function () {
            const choice = this.getAttribute('data-choice');
            makeChoice(choice);
        });
    });

    if (goBackButton) {
        goBackButton.addEventListener('click', goBack);
    }

    function makeChoice(choice) {
        fetch('/make_choice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `choice=${encodeURIComponent(choice)}`
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert(data.message);
                }
            })
            .catch(error => console.error('Error:', error));
    }

    function goBack() {
        fetch('/go_back', {
            method: 'POST'
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert(data.message);
                }
            })
            .catch(error => console.error('Error:', error));
    }
});