document.addEventListener('DOMContentLoaded', function () {
    const careerList = document.getElementById('career-list');
    const randomCareerButton = document.getElementById('random-career');
    const selectedCareer = document.getElementById('selected-career');

    // 職業リストを取得して表示する関数
    function fetchAndDisplayCareers() {
        fetch('/api/careers')
            .then(response => response.json())
            .then(careers => {
                careerList.innerHTML = '';
                careers.forEach(career => {
                    const careerElement = document.createElement('div');
                    careerElement.className = 'career-item';
                    careerElement.innerHTML = `
                        <h3>${career.name}</h3>
                        <p>${career.description}</p>
                        <button onclick="selectCareer(${career.id})">選択</button>
                    `;
                    careerList.appendChild(careerElement);
                });
            })
            .catch(error => console.error('Error:', error));
    }

    // 特定の職業を選択する関数
    window.selectCareer = function (careerId) {
        fetch(`/api/careers/${careerId}`)
            .then(response => response.json())
            .then(career => {
                displaySelectedCareer(career);
            })
            .catch(error => console.error('Error:', error));
    }

    // ランダムな職業を選択する関数
    function selectRandomCareer() {
        fetch('/api/random_career')
            .then(response => response.json())
            .then(career => {
                displaySelectedCareer(career);
            })
            .catch(error => console.error('Error:', error));
    }

    // 選択された職業を表示する関数
    function displaySelectedCareer(career) {
        selectedCareer.innerHTML = `
            <h3>選択された職業: ${career.name}</h3>
            <p>${career.description}</p>
            <button onclick="startCareerSimulation(${career.id})">このキャリアを始める</button>
        `;
    }

    // キャリアシミュレーションを開始する関数
    window.startCareerSimulation = function (careerId) {
        // ユーザーIDを取得する必要があります。セッションやローカルストレージから取得するか、
        // サーバーサイドでレンダリング時に埋め込むなどの方法があります。
        const userId = getCurrentUserId(); // この関数は適切に実装する必要があります
        window.location.href = `/simulation_result/${userId}/${careerId}`;
    }

    // イベントリスナーの設定
    document.addEventListener('DOMContentLoaded', fetchAndDisplayCareers);
    randomCareerButton.addEventListener('click', selectRandomCareer);
});

// ユーザーIDを取得する関数（この実装は環境に応じて適切に修正してください）
function getCurrentUserId() {
    // 例: ローカルストレージからユーザーIDを取得
    return localStorage.getItem('userId');
    // または、サーバーサイドでレンダリング時に埋め込んだ要素から取得
    // return document.getElementById('current-user-id').value;
}