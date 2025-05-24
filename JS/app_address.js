// Инициализация карты
const map = L.map('map', {
    attributionControl: false // Можно оставить или убрать, если вам нужен контроль атрибуции
}).setView([42.87, 74.59], 6); // Центр: Бишкек, начальный зум

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
}).addTo(map);

const companyListEl = document.getElementById('company-list');
const searchInput = document.getElementById('company-search');

let allCompanies = []; // Храним все компании
let companyMarkers = {}; // Маркеры для существующих компаний

// Элементы для поиска адреса на карте (на странице юзера или админа)
const addressInputMapSearch = document.getElementById('address_input_map_search'); // Поле поиска адреса на карте
const geocodeButtonMapSearch = document.getElementById('geocode_button_map_search'); // Кнопка поиска на карте
let geocodeMarkerMapSearch; // Маркер для найденного адреса при поиске на карте

// --- Функции для работы с компаниями ---

/**
 * Загружает компании с сервера.
 * @param {string} filterQuery - Необязательный запрос для фильтрации.
 */
async function loadCompanies(filterQuery = '') {
    if (companyListEl) {
        companyListEl.innerHTML = '<li>Загрузка компаний...</li>';
    }
    try {
        const url = filterQuery ? `/companies?q=${encodeURIComponent(filterQuery)}` : '/companies';
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        allCompanies = await response.json(); // Сохраняем все загруженные компании
        if (companyListEl) {
            renderCompanyList(allCompanies); // Изначально рендерим все компании
        }
        addMarkersToMap(allCompanies);
    } catch (error) {
        console.error("Ошибка при загрузке компаний:", error);
        if (companyListEl) {
            companyListEl.innerHTML = '<li>Ошибка загрузки компаний.</li>';
        }
    }
}

/**
 * Рендерит список компаний.
 * @param {Array<object>} companiesToRender - Компании для отображения в списке.
 */
function renderCompanyList(companiesToRender) {
    companyListEl.innerHTML = '';
    if (companiesToRender.length === 0) {
        companyListEl.innerHTML = '<li>Компании не найдены.</li>';
        return;
    }
    companiesToRender.forEach(company => {
        const li = document.createElement('li');
        li.classList.add('company-list-item');

        const companyNameSpan = document.createElement('span');
        companyNameSpan.textContent = company.company_name;
        companyNameSpan.classList.add('company-name-link');

        // Обработчик клика для названия компании в списке: центрировать карту и открыть попап
        companyNameSpan.addEventListener('click', () => {
            const marker = companyMarkers[company.id];
            if (marker) {
                map.setView(marker.getLatLng(), 13); // Устанавливаем зум 13 для приближения
                marker.openPopup();
            }
        });

        const detailsButton = document.createElement('button');
        detailsButton.textContent = 'Подробнее';
        detailsButton.classList.add('details-button');

        // Обработчик клика для кнопки "Подробнее": перенаправление на страницу деталей
        detailsButton.addEventListener('click', () => {
            window.location.href = `/company_detail/${company.id}`;
        });

        li.appendChild(companyNameSpan);
        li.appendChild(detailsButton);
        companyListEl.appendChild(li);
    });
}

/**
 * Добавляет маркеры компаний на карту.
 * @param {Array<object>} companiesToAdd - Компании для добавления маркеров.
 */
function addMarkersToMap(companiesToAdd) {
    // Удаляем все предыдущие маркеры компаний перед добавлением новых
    for (const id in companyMarkers) {
        if (companyMarkers[id] && map.hasLayer(companyMarkers[id])) {
            map.removeLayer(companyMarkers[id]);
        }
    }
    companyMarkers = {}; // Очищаем объект маркеров

    companiesToAdd.forEach(company => {
        const { id, latitude, longitude, company_name, product_name, stage } = company;
        if (latitude !== null && longitude !== null && !isNaN(latitude) && !isNaN(longitude)) {
            const marker = L.marker([latitude, longitude])
                .addTo(map)
                .bindPopup(`<b>${company_name}</b><br>${product_name}<br>Этап: ${stage}`); // Удалена ссылка из попапа

            // Обработчик клика на маркер: просто открыть попап и центрировать карту
            marker.on('click', function() {
                map.setView(marker.getLatLng(), 13); // Центрируем карту
                marker.openPopup(); // Открываем попап
                // Перенаправление на /company_detail/${id} теперь только по кнопке "Подробнее"
            });

            companyMarkers[id] = marker;
        } else {
            console.warn(`Пропущен поставщик ${company_name} (ID: ${id}) с некорректными координатами.`);
        }
    });
}

// Фильтрация списка при вводе в поле поиска (только если на странице есть searchInput)
if (searchInput) {
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase();
        const filtered = allCompanies.filter(c =>
            c.company_name.toLowerCase().includes(query)
        );
        renderCompanyList(filtered);
    });
}

// --- Логика поиска адреса на карте (для отдельного блока поиска, например на user.html) ---
if (geocodeButtonMapSearch && addressInputMapSearch) {
    geocodeButtonMapSearch.addEventListener('click', async () => {
        const address = addressInputMapSearch.value;
        if (!address) {
            alert("Пожалуйста, введите адрес для поиска.");
            return;
        }

        try {
            const response = await fetch(`/search?q=${encodeURIComponent(address)}`);
            const data = await response.json();

            if (response.ok && data.lat && data.lon) {
                const { lat, lon, name } = data;
                if (geocodeMarkerMapSearch) {
                    map.removeLayer(geocodeMarkerMapSearch);
                }
                geocodeMarkerMapSearch = L.marker([lat, lon])
                    .addTo(map)
                    .bindPopup(name || address)
                    .openPopup();
                map.setView([lat, lon], 13);
            } else {
                alert(data.error || "Адрес не найден.");
            }
        } catch (error) {
            console.error("Ошибка при поиске адреса на карте:", error);
            alert("Произошла ошибка при поиске адреса на карте. Проверьте подключение или попробуйте еще раз.");
        }
    });
}


// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Загружаем компании только если мы на user.html (или другой странице, где нужен список)
    if (document.getElementById('company-list')) {
        loadCompanies();
    }
    
    const addressInputForm = document.getElementById('address_input'); // Поле ввода адреса в форме админа
    const geocodeButtonForm = document.getElementById('geocode_button'); // Кнопка геокодирования в форме админа
    const coordinatesDisplayForm = document.getElementById('coordinates_display'); // Отображение координат в форме админа
    let geocodeMarkerForm; // Маркер для найденного адреса в форме админа

    if (geocodeButtonForm && addressInputForm && coordinatesDisplayForm) { // Проверяем наличие элементов
        geocodeButtonForm.addEventListener('click', async () => {
            const address = addressInputForm.value;
            if (!address) {
                alert("Пожалуйста, введите адрес для поиска.");
                return;
            }

            coordinatesDisplayForm.textContent = 'Координаты на карте: поиск...';

            try {
                const response = await fetch(`/search?q=${encodeURIComponent(address)}`);
                const data = await response.json();

                if (response.ok && data.lat && data.lon) {
                    const { lat, lon, name } = data;
                    coordinatesDisplayForm.textContent = `Координаты на карте: Широта ${lat.toFixed(6)}, Долгота ${lon.toFixed(6)}`;

                    if (geocodeMarkerForm) {
                        map.removeLayer(geocodeMarkerForm);
                    }
                    geocodeMarkerForm = L.marker([lat, lon])
                        .addTo(map)
                        .bindPopup(name || address)
                        .openPopup();
                    map.setView([lat, lon], 13);
                } else {
                    const errorMessage = data.error || "Адрес не найден или произошла ошибка.";
                    alert(errorMessage);
                    coordinatesDisplayForm.textContent = 'Координаты на карте: Адрес не найден';
                }
            } catch (error) {
                console.error("Ошибка при геокодировании адреса:", error);
                alert("Произошла ошибка при поиске адреса. Проверьте подключение или попробуйте еще раз.");
                coordinatesDisplayForm.textContent = 'Координаты на карте: Ошибка при поиске';
            }
        });
    }
});