if (window.AOS) {
    AOS.init({ duration: 1000, once: true });
}

// Keep scroll styling theme-aware by leaving colors to CSS variables.
window.addEventListener("scroll", function () {
    const navbar = document.querySelector(".site-navbar");
    if (navbar) navbar.classList.toggle("is-scrolled", window.scrollY > 80);
});


// Counter Animation

const counters=document.querySelectorAll(".counter");

counters.forEach(counter=>{

    const update=()=>{

        const dataTarget=counter.getAttribute("data-target");
        const target=+(dataTarget===null?counter.innerText.replace("+",""):dataTarget);
        const dataSuffix=counter.getAttribute("data-suffix");
        const suffix=dataSuffix===null?"+":dataSuffix;

        const count=+counter.getAttribute("data-count") || 0;

        const speed=60;

        const increment=Math.ceil(target/speed);

        if(count<target){

            const newCount=count+increment;

            counter.setAttribute("data-count",newCount);

            counter.innerText=newCount+suffix;

            setTimeout(update,25);

        }

        else{

            counter.innerText=target+suffix;

        }

    }

    update();

});



// Smooth Scroll

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({ behavior: 'smooth' });
    });
});

// Leaflet map with complaint markers and place search.
if (document.querySelector('[data-map-mode="leaflet"]') && window.L) {
    const mapElement = document.getElementById('city-map');
    if (mapElement) {
        const map = L.map('city-map', { zoomControl: true }).setView([51.5074, -0.1278], 11);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 19,
        }).addTo(map);

        const rawMapData = document.getElementById('map-data');
        if (rawMapData) {
            try {
                const mapPoints = JSON.parse(rawMapData.textContent || '[]');
                const mapUiElement = document.getElementById('map-ui-data');
                const mapUi = mapUiElement ? JSON.parse(mapUiElement.textContent) : {};
                const bounds = [];
                const markers = [];
                const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, character => ({
                    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
                }[character]));
                mapPoints.forEach(point => {
                    if (!point.coords || point.coords.length !== 2) {
                        return;
                    }
                    const marker = L.circleMarker(point.coords, {
                        radius: 8,
                        color: point.color || '#3ea6ff',
                        fillColor: point.color || '#3ea6ff',
                        fillOpacity: 0.85,
                        weight: 2,
                    }).addTo(map);
                    marker.bindPopup(`<strong>${escapeHtml(point.title)}</strong><br />${escapeHtml(point.location)}<br /><em>${escapeHtml(point.category)}</em><br />${escapeHtml(mapUi.status)} ${escapeHtml(point.status)}`);
                    bounds.push(point.coords);
                    markers.push({ point, marker });
                });
                if (bounds.length > 0) {
                    map.fitBounds(bounds, { padding: [40, 40] });
                }

                const searchForm = document.getElementById('map-search-form');
                const searchInput = document.getElementById('map-search-input');
                const searchStatus = document.getElementById('map-search-status');
                if (searchForm && searchInput && searchStatus) {
                    searchForm.addEventListener('submit', async (event) => {
                        event.preventDefault();
                        const query = searchInput.value.trim();
                        if (!query) return;
                        const matchingReports = markers.filter(({ point }) =>
                            `${point.title} ${point.location} ${point.category}`.toLowerCase().includes(query.toLowerCase())
                        );
                        if (matchingReports.length) {
                            const matchingBounds = matchingReports.map(({ point }) => point.coords);
                            map.fitBounds(matchingBounds, { padding: [50, 50], maxZoom: 15 });
                            matchingReports[0].marker.openPopup();
                            const message = matchingReports.length === 1 ? mapUi.reportedNearSingular : mapUi.reportedNearPlural;
                            searchStatus.textContent = `${matchingReports.length} ${message.replace('%(query)s', query)}`;
                            return;
                        }
                        searchStatus.textContent = mapUi.searchingPlace.replace('%(query)s', query);
                        try {
                            const response = await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(query)}`, { headers: { Accept: 'application/json' } });
                            const places = await response.json();
                            if (!places.length) {
                                searchStatus.textContent = mapUi.placeNotFound.replace('%(query)s', query);
                                return;
                            }
                            const place = places[0];
                            const position = [Number(place.lat), Number(place.lon)];
                            map.setView(position, 14);
                            L.marker(position).addTo(map).bindPopup(`<strong>${escapeHtml(place.display_name)}</strong><br />${escapeHtml(mapUi.noComplaintAtPlace)}`).openPopup();
                            searchStatus.textContent = mapUi.showingPlace.replace('%(place)s', place.display_name);
                        } catch (error) {
                            searchStatus.textContent = mapUi.searchUnavailable;
                        }
                    });
                }
            } catch (err) {
                console.error('Failed to load map data', err);
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('weather-search-form');
    const searchInput = document.getElementById('weather-city');
    const loading = document.getElementById('weather-loading');
    const refreshButton = document.getElementById('weather-refresh');
    const unitButtons = document.querySelectorAll('[data-weather-unit]');
    const hourlyToggle = document.getElementById('forecast-hourly-toggle');
    const hourlyPanel = document.getElementById('forecast-hourly');
    const forecastRows = document.querySelectorAll('[data-forecast-index]');
    const forecastDataElement = document.getElementById('weather-forecast-data');
    const weatherUiElement = document.getElementById('weather-ui-data');
    const weatherUi = weatherUiElement ? JSON.parse(weatherUiElement.textContent) : {};
    const forecastData = forecastDataElement ? JSON.parse(forecastDataElement.textContent) : [];
    let temperatureUnit = 'C';

    const formatTemperature = (celsius) => {
        const value = temperatureUnit === 'F' ? (Number(celsius) * 9 / 5) + 32 : Number(celsius);
        return Math.round(value);
    };

    const updateTemperatures = () => {
        document.querySelectorAll('[data-celsius]').forEach((element) => {
            const celsius = Number(element.dataset.celsius);
            if (Number.isFinite(celsius)) {
                element.textContent = `${formatTemperature(celsius)}${element.matches('.forecast-temperatures strong, .forecast-temperatures span') ? '°' : ''}`;
            }
        });
        document.querySelectorAll('[data-weather-unit-label]').forEach((element) => {
            element.textContent = `°${temperatureUnit}`;
        });
    };

    const updateHourlyForecast = (items) => {
        if (!hourlyPanel) return;
        hourlyPanel.replaceChildren();
        items.forEach((item) => {
            const hour = document.createElement('div');
            hour.className = 'forecast-hour';
            const time = document.createElement('span');
            time.textContent = item.time;
            hour.append(time);
            if (item.icon) {
                const icon = document.createElement('img');
                icon.src = `https://openweathermap.org/img/wn/${item.icon}.png`;
                icon.alt = '';
                icon.width = 30;
                icon.height = 30;
                hour.append(icon);
            }
            const temperature = document.createElement('strong');
            temperature.textContent = `${formatTemperature(item.temperature)}°${temperatureUnit}`;
            hour.append(temperature);
            hourlyPanel.append(hour);
        });
    };

    const selectForecastDay = (index) => {
        const day = forecastData[index];
        if (!day) return;
        forecastRows.forEach((row) => {
            const selected = Number(row.dataset.forecastIndex) === index;
            row.classList.toggle('is-selected', selected);
            row.setAttribute('aria-pressed', String(selected));
        });
        document.getElementById('forecast-selected-date').textContent = day.date_label;
        document.getElementById('forecast-selected-description').textContent = day.description;
        document.getElementById('forecast-selected-rain').textContent = day.precipitation;
        document.getElementById('forecast-selected-wind').textContent = day.wind_speed == null ? '--' : Number(day.wind_speed).toFixed(1);
        updateHourlyForecast(day.hourly || []);
    };

    if (searchForm) {
        searchForm.addEventListener('submit', (event) => {
            if (!searchInput.value.trim()) {
                event.preventDefault();
                searchInput.focus();
                return;
            }
            if (loading) loading.hidden = false;
        });
    }

    refreshButton?.addEventListener('click', () => {
        if (!searchForm) return;
        let refreshToken = searchForm.querySelector('input[name="_refresh"]');
        if (!refreshToken) {
            refreshToken = document.createElement('input');
            refreshToken.type = 'hidden';
            refreshToken.name = '_refresh';
            searchForm.append(refreshToken);
        }
        refreshToken.value = String(Date.now());
        searchForm.requestSubmit();
    });

    unitButtons.forEach((button) => {
        button.addEventListener('click', () => {
            temperatureUnit = button.dataset.weatherUnit;
            unitButtons.forEach((unitButton) => {
                unitButton.setAttribute('aria-pressed', String(unitButton === button));
            });
            updateTemperatures();
            const selectedIndex = Array.from(forecastRows).findIndex((row) => row.getAttribute('aria-pressed') === 'true');
            if (selectedIndex >= 0) updateHourlyForecast(forecastData[selectedIndex]?.hourly || []);
        });
    });

    forecastRows.forEach((row) => {
        row.addEventListener('click', () => selectForecastDay(Number(row.dataset.forecastIndex)));
    });

    hourlyToggle?.addEventListener('click', () => {
        const expanded = hourlyToggle.getAttribute('aria-expanded') === 'true';
        hourlyToggle.setAttribute('aria-expanded', String(!expanded));
        hourlyPanel.hidden = expanded;
        hourlyToggle.querySelector('span').textContent = expanded ? weatherUi.showHourly : weatherUi.hideHourly;
        hourlyToggle.querySelector('i').className = expanded ? 'bi bi-chevron-down' : 'bi bi-chevron-up';
    });

    updateTemperatures();
    if (forecastRows.length) selectForecastDay(0);
});

document.addEventListener('DOMContentLoaded', () => {
    const chatPage = document.querySelector('.assistant-page');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const fileInput = document.getElementById('chat-attachment');
    const filePreview = document.getElementById('chat-attachment-preview');
    const recentActions = document.getElementById('recent-chat-actions');
    const clearHistory = document.getElementById('clear-chat-history');
    const locationButton = document.getElementById('use-my-location');
    const locationStatus = document.getElementById('location-status');
    const chatbotMessagesElement = document.getElementById('chatbot-messages');
    const chatbotMessages = chatbotMessagesElement ? JSON.parse(chatbotMessagesElement.textContent) : {};

    if (chatPage && chatForm && chatInput && chatMessages) {
        const historyKey = 'citypulse-chat-recent';
        const attachmentMaxSize = 10 * 1024 * 1024;
        const aiReady = chatPage.dataset.aiReady === 'true';
        const conversation = [];
        const sendButton = chatForm.querySelector('[type="submit"]');
        const csrfToken = chatForm.querySelector('[name="csrfmiddlewaretoken"]')?.value;
        const assistantStatus = document.getElementById('assistant-status');
        let attachment = null;
        let currentObjectUrl = null;
        let actionHistory = [];
        let requestPending = false;

        const reportUrl = chatPage.dataset.reportUrl;
        const mapUrl = chatPage.dataset.mapUrl;
        const weatherUrl = chatPage.dataset.weatherUrl;
        const reportsUrl = chatPage.dataset.reportsUrl;

        const readHistory = () => {
            try {
                const value = JSON.parse(localStorage.getItem(historyKey) || '[]');
                return Array.isArray(value) ? value.slice(0, 6) : [];
            } catch (error) {
                return [];
            }
        };

        const saveHistory = () => {
            try {
                localStorage.setItem(historyKey, JSON.stringify(actionHistory.slice(0, 6)));
            } catch (error) {
                // Keep the current conversation usable if storage is unavailable.
            }
        };

        const renderHistory = () => {
            if (!recentActions) return;
            recentActions.replaceChildren();
            if (!actionHistory.length) {
                const empty = document.createElement('p');
                empty.className = 'assistant-recent-empty';
                empty.textContent = chatbotMessages.emptyHistory;
                recentActions.append(empty);
                return;
            }

            actionHistory.forEach((item) => {
                const button = document.createElement('button');
                button.className = 'assistant-recent-item';
                button.type = 'button';
                button.dataset.replayPrompt = item.text;
                button.dataset.replayIntent = item.intent || '';
                const label = document.createElement('span');
                label.textContent = item.text;
                const time = document.createElement('small');
                time.textContent = item.time;
                button.append(label, time);
                recentActions.append(button);
            });
        };

        const addHistory = (text, intent) => {
            actionHistory = [{ text, intent, time: new Date().toLocaleTimeString(document.documentElement.lang, { hour: 'numeric', minute: '2-digit' }) }, ...actionHistory]
                .filter((item, index, items) => items.findIndex((entry) => entry.text === item.text) === index)
                .slice(0, 6);
            saveHistory();
            renderHistory();
        };

        const scrollConversation = () => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        };

        const addMessage = (text, type, attachmentName = '') => {
            const line = document.createElement('article');
            line.className = `chat-line chat-line--${type}`;
            const avatar = document.createElement('span');
            avatar.className = 'chat-avatar';
            const icon = document.createElement('i');
            icon.className = type === 'assistant' ? 'bi bi-robot' : 'bi bi-person-fill';
            icon.setAttribute('aria-hidden', 'true');
            avatar.append(icon);

            const content = document.createElement('div');
            const bubble = document.createElement('div');
            bubble.className = `chat-message chat-message--${type}`;
            const paragraph = document.createElement('p');
            paragraph.textContent = text;
            bubble.append(paragraph);

            if (attachmentName) {
                const attachmentNote = document.createElement('span');
                attachmentNote.className = 'chat-attachment-note';
                attachmentNote.textContent = chatbotMessages.fileKept.replace('%(name)s', attachmentName);
                bubble.append(attachmentNote);
            }

            content.append(bubble);
            const time = document.createElement('time');
            time.className = 'chat-time';
            time.dateTime = new Date().toISOString();
            time.textContent = new Date().toLocaleTimeString(document.documentElement.lang, { hour: 'numeric', minute: '2-digit' });
            content.append(time);
            line.append(avatar, content);
            chatMessages.append(line);
            scrollConversation();
            return line;
        };

        const getReply = (text, intent = '') => {
            if (intent === 'emergency') {
                return { text: chatbotMessages.emergencyReply, links: [{ label: chatbotMessages.openReport, href: reportUrl }] };
            }
            if (intent === 'garbage' || intent === 'report') {
                return { text: chatbotMessages.garbageReply, links: [{ label: chatbotMessages.reportIssue, href: reportUrl }, { label: chatbotMessages.viewHotspots, href: mapUrl }] };
            }
            if (intent === 'map') {
                return { text: chatbotMessages.mapReply, links: [{ label: chatbotMessages.openLiveMap, href: mapUrl }] };
            }
            if (intent === 'road') {
                return { text: chatbotMessages.roadReply, links: [{ label: chatbotMessages.startReport, href: reportUrl }, { label: chatbotMessages.openMap, href: mapUrl }] };
            }
            if (intent === 'water') {
                return { text: chatbotMessages.waterReply, links: [{ label: chatbotMessages.reportWaterIssue, href: reportUrl }] };
            }
            const request = text.toLowerCase();
            if (/emergency|urgent|danger|accident|fire/.test(request)) {
                return {
                    text: chatbotMessages.emergencyReply,
                    links: [{ label: chatbotMessages.openReport, href: reportUrl }],
                };
            }
            if (/garbage|waste|trash|litter|cleanliness/.test(request)) {
                return {
                    text: chatbotMessages.garbageReply,
                    links: [{ label: chatbotMessages.reportIssue, href: reportUrl }, { label: chatbotMessages.viewHotspots, href: mapUrl }],
                };
            }
            if (/road|pothole|street|traffic|light/.test(request)) {
                return {
                    text: chatbotMessages.roadReply,
                    links: [{ label: chatbotMessages.startReport, href: reportUrl }, { label: chatbotMessages.openMap, href: mapUrl }],
                };
            }
            if (/water|pipe|leak|supply|drain/.test(request)) {
                return {
                    text: chatbotMessages.waterReply,
                    links: [{ label: chatbotMessages.reportWaterIssue, href: reportUrl }],
                };
            }
            if (/map|hotspot|nearby|location/.test(request)) {
                return {
                    text: chatbotMessages.mapReply,
                    links: [{ label: chatbotMessages.openLiveMap, href: mapUrl }],
                };
            }
            if (/weather|rain|wind|temperature|forecast/.test(request)) {
                return {
                    text: chatbotMessages.weatherReply,
                    links: [{ label: chatbotMessages.checkCityWeather, href: weatherUrl }],
                };
            }
            if (/my report|track|status|complaint|submitted/.test(request)) {
                return {
                    text: chatbotMessages.reportsReply,
                    links: [{ label: chatbotMessages.viewMyReports, href: reportsUrl }],
                };
            }
            return {
                text: chatbotMessages.generalReply,
                links: [{ label: chatbotMessages.createReport, href: reportUrl }, { label: chatbotMessages.openLiveMap, href: mapUrl }],
            };
        };

        const addReplyLinks = (line, links) => {
            if (!links.length) return;
            const bubble = line.querySelector('.chat-message');
            const actions = document.createElement('div');
            actions.className = 'chat-response-actions';
            links.forEach((item) => {
                const link = document.createElement('a');
                link.className = 'chat-response-link';
                link.href = item.href;
                link.textContent = item.label;
                actions.append(link);
            });
            bubble.append(actions);
            scrollConversation();
        };

        const clearAttachment = () => {
            if (currentObjectUrl) URL.revokeObjectURL(currentObjectUrl);
            currentObjectUrl = null;
            attachment = null;
            if (fileInput) fileInput.value = '';
            if (filePreview) {
                filePreview.replaceChildren();
                filePreview.hidden = true;
            }
        };

        const showAttachment = (file) => {
            if (!filePreview) return;
            filePreview.replaceChildren();
            const detail = document.createElement('span');
            detail.className = 'chat-attachment-detail';
            if (file.type.startsWith('image/')) {
                currentObjectUrl = URL.createObjectURL(file);
                const image = document.createElement('img');
                image.src = currentObjectUrl;
                image.alt = chatbotMessages.selectedPreview;
                detail.append(image);
            }
            const name = document.createElement('span');
            name.textContent = `${file.name} · ${(file.size / 1024).toFixed(0)} KB`;
            detail.append(name);
            const remove = document.createElement('button');
            remove.type = 'button';
            remove.className = 'composer-tool';
            remove.setAttribute('aria-label', chatbotMessages.removeAttachment);
            remove.innerHTML = '<i class="bi bi-x-lg" aria-hidden="true"></i>';
            remove.addEventListener('click', clearAttachment);
            filePreview.append(detail, remove);
            filePreview.hidden = false;
        };

        const sendChat = async (text, intent = '') => {
            const cleanText = text.trim();
            if (!cleanText || requestPending) {
                chatInput.focus();
                return;
            }
            const attachedName = attachment?.name || '';
            addMessage(cleanText, 'user', attachedName);
            conversation.push({ role: 'user', content: cleanText });
            addHistory(cleanText, intent);
            chatInput.value = '';
            chatInput.style.height = 'auto';
            clearAttachment();

            const typing = document.createElement('article');
            typing.className = 'chat-line chat-line--assistant chat-line--typing';
            typing.setAttribute('aria-label', chatbotMessages.assistantPreparing);
            typing.innerHTML = '<span class="chat-avatar"><i class="bi bi-robot" aria-hidden="true"></i></span><div class="chat-message chat-message--assistant chat-typing"><span></span><span></span><span></span></div>';
            chatMessages.append(typing);
            requestPending = true;
            if (sendButton) sendButton.disabled = true;
            scrollConversation();

            try {
                let reply;
                if (aiReady) {
                    const response = await fetch(chatPage.dataset.chatEndpoint, {
                        method: 'POST',
                        credentials: 'same-origin',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken,
                        },
                        body: JSON.stringify({ messages: conversation.slice(-12) }),
                    });
                    const payload = await response.json();
                    if (!response.ok) throw new Error(payload.error || chatbotMessages.serviceUnavailable);
                    reply = { text: payload.reply, links: [] };
                } else {
                    await new Promise((resolve) => window.setTimeout(resolve, 350));
                    reply = getReply(cleanText, intent);
                }

                typing.remove();
                const line = addMessage(reply.text, 'assistant');
                addReplyLinks(line, reply.links);
                conversation.push({ role: 'assistant', content: reply.text });
            } catch (error) {
                typing.remove();
                const line = addMessage(error.message || chatbotMessages.serviceUnavailable, 'assistant');
                addReplyLinks(line, [{ label: chatbotMessages.createReport, href: reportUrl }, { label: chatbotMessages.openLiveMap, href: mapUrl }]);
            } finally {
                requestPending = false;
                if (sendButton) sendButton.disabled = false;
                chatInput.focus();
            }
        };

        document.querySelectorAll('[data-chat-prompt]').forEach((button) => {
            button.addEventListener('click', () => sendChat(button.dataset.chatPrompt || '', button.dataset.chatIntent || ''));
        });

        recentActions?.addEventListener('click', (event) => {
            const button = event.target.closest('[data-replay-prompt]');
            if (button) sendChat(button.dataset.replayPrompt || '', button.dataset.replayIntent || '');
        });

        chatForm.addEventListener('submit', (event) => {
            event.preventDefault();
            sendChat(chatInput.value);
        });

        chatInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                chatForm.requestSubmit();
            }
        });

        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = `${Math.min(chatInput.scrollHeight, 140)}px`;
        });

        document.getElementById('attach-chat-file')?.addEventListener('click', () => {
            if (fileInput) fileInput.accept = 'image/*,.pdf,.txt';
            fileInput?.click();
        });
        document.getElementById('attach-chat-image')?.addEventListener('click', () => {
            if (fileInput) fileInput.accept = 'image/*';
            fileInput?.click();
        });

        fileInput?.addEventListener('change', () => {
            const file = fileInput.files?.[0];
            if (!file) return;
            if (file.size > attachmentMaxSize) {
                clearAttachment();
                filePreview.hidden = false;
                filePreview.textContent = chatbotMessages.chooseSmallerFile;
                return;
            }
            attachment = file;
            showAttachment(file);
        });

        locationButton?.addEventListener('click', () => {
            if (!navigator.geolocation) {
                locationStatus.textContent = chatbotMessages.locationUnavailable;
                return;
            }
            locationButton.disabled = true;
            locationStatus.textContent = chatbotMessages.waitingForLocation;
            navigator.geolocation.getCurrentPosition((position) => {
                locationButton.disabled = false;
                const latitude = position.coords.latitude.toFixed(4);
                const longitude = position.coords.longitude.toFixed(4);
                locationStatus.textContent = chatbotMessages.locationFound.replace('%(latitude)s', latitude).replace('%(longitude)s', longitude);
                const reportPrompt = chatbotMessages.locationReportPrompt
                    .replace('%(latitude)s', latitude)
                    .replace('%(longitude)s', longitude);
                sendChat(reportPrompt, 'report');
            }, () => {
                locationButton.disabled = false;
                locationStatus.textContent = chatbotMessages.locationDenied;
            }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 });
        });

        clearHistory?.addEventListener('click', () => {
            actionHistory = [];
            saveHistory();
            renderHistory();
            chatMessages.querySelectorAll('.chat-line:not(:first-child)').forEach((line) => line.remove());
            clearAttachment();
            if (locationStatus) locationStatus.textContent = chatbotMessages.historyCleared;
        });

        actionHistory = readHistory();
        renderHistory();
        const initialTime = chatMessages.querySelector('[data-chat-time]');
        if (initialTime) initialTime.textContent = new Date().toLocaleTimeString(document.documentElement.lang, { hour: 'numeric', minute: '2-digit' });
    }

    const imageInput = document.querySelector('input[type="file"]:not(#chat-attachment)');
    const imagePreview = document.getElementById('image-preview');
    imageInput?.addEventListener('change', () => {
        const file = imageInput.files?.[0];
        if (!file || !imagePreview) return;
        const imageUrl = URL.createObjectURL(file);
        imagePreview.innerHTML = `<img src="${imageUrl}" alt="${imagePreview.dataset.previewLabel}"><span>📷 ${file.name}</span>`;
        imagePreview.classList.remove('d-none');
    });
});
