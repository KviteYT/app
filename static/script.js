const form = document.querySelector('form');
const resultsDiv = document.getElementById('results');

form.addEventListener('submit', (event) => {
    event.preventDefault();

    const budget = document.getElementById('budget').value;
    const application = document.getElementById('application').value;
    const performanceLevel = document.getElementById('performance_level').value;

    fetch('/select', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `budget=${budget}&application=${application}&performance_level=${performanceLevel}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            resultsDiv.innerHTML = `<p class="error">${data.error}</p>`;
        } else {
            resultsDiv.innerHTML = `
                <h2>Подборка комплектующих:</h2>
                <ul>
                    <li><strong>Процессор:</strong> ${data.cpu.name} (${data.cpu.price} руб.)</li>
                    <li><strong>Материнская плата:</strong> ${data.motherboard.name} (${data.motherboard.price} руб.)</li>
                    <li><strong>Оперативная память:</strong> ${data.ram.name} (${data.ram.price} руб.)</li>
                    <li><strong>Видеокарта:</strong> ${data.gpu.name} (${data.gpu.price} руб.)</li>
                    <li><strong>Хранилище:</strong> ${data.storage.name} (${data.storage.price} руб.)</li>
                    <li><strong>Блок питания:</strong> ${data.psu.name} (${data.psu.price} руб.)</li>
                </ul>
            `;
        }
    })
    .catch(error => {
        resultsDiv.innerHTML = `<p class="error">Ошибка: ${error}</p>`;
    });
});

