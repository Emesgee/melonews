// Initialize the map
var map = L.map('map').setView([31.5, 34.8], 3);

// Add tile layers to the map
var darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://carto.com/attributions">CARTO</a>',
    opacity: 0.7
}).addTo(map);

var openTopoMapLayer = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
    attribution: 'Map data: &copy; <a href="https://www.opentopomap.org">OpenTopoMap</a> contributors, ' +
        '<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>'
});

var openStreetMapLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

var worldStreetMapLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/{variant}/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri & OpenStreetMap contributors',
    variant: 'World_Street_Map'
}).addTo(map);

var ersriWorldImageryMapLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/{variant}/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri & OpenStreetMap contributors',
    variant: 'World_Imagery'
}).addTo(map);

var humanitarianMapLayer = L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors, Humanitarian OpenStreetMap Team'
}).addTo(map);

var roadmapLayer = L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
    attribution: '&copy; Google',
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
}).addTo(map);

var satelliteMapLayer = L.tileLayer('https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
    attribution: '&copy; Google',
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
}).addTo(map);

// Define a baseMaps object to hold our base layers
var baseMaps = {
    "Carto Dark": darkLayer,
    "OpenTopoMap": openTopoMapLayer,
    "OpenStreetMap": openStreetMapLayer,
    "World Street Map": worldStreetMapLayer,
    "Esri World Imagery Map": ersriWorldImageryMapLayer,
    "Humanitarian Map": humanitarianMapLayer,
    "Roadmap": roadmapLayer,
    "Satellite Map": satelliteMapLayer
};

// Add layer control
L.control.layers(baseMaps).addTo(map);

// Create a marker cluster group
var markers = L.markerClusterGroup();

// Store original marker text to use for translations
var leafletMarkers = [];

// Function to update sidebar with marker details
function updateSidebar(marker) {
    var sidebarContent = document.getElementById('sidebar-content');
    sidebarContent.innerHTML = `
        <div class="sidebar-item">
            <img src="https://ghadban.tech/static/quanti_logo_watermelon.jpeg" alt="Logo" style="max-width: 25%; height: auto; margin-bottom: 0px; top:0;"><br>
            <strong>Date:</strong> ${marker.date}<br>
            <strong>Time:</strong> ${marker.time}<br><br>
            <strong>Title:</strong> ${marker.title}<br><br>
            <strong>City:</strong> ${marker.city}<br><br>
            <strong>Message:</strong> ${marker.message}<br><br>
            <strong>Latitude:</strong> ${marker.latitude.toFixed(4)}<br>
            <strong>Longitude:</strong> ${marker.longitude.toFixed(4)}<br><br>
            <video width="100%" controls>
                <source src="${marker.video}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
    `;
}

// Function to fetch translation from an API
async function fetchTranslation(text, targetLanguage) {
    const response = await fetch(`https://api.translationapi.com/translate?text=${encodeURIComponent(text)}&to=${targetLanguage}`);
    const data = await response.json();
    return data.translation;
}

// Update marker text based on selected language
document.getElementById('language').addEventListener('change', async function(event) {
    var selectedLanguage = event.target.value;
    for (let leafletMarker of leafletMarkers) {
        const translatedText = await fetchTranslation(leafletMarker.text, selectedLanguage);
        leafletMarker.marker.setPopupContent(translatedText);
    }
});

// Function to update bottom sidebar with marker message
function updateBottomSidebar(marker) {
    var bottomSidebarContent = document.getElementById('bottom-sidebar-content');
    bottomSidebarContent.innerHTML = `
        <div>
            <strong style="font-size: 1.5em;">Message:</strong> <span style="font-size: 1.5em;">${marker.message}</span>
        </div>
    `;
}

// Fetch data from Flask route '/data' and add markers to the map
fetch('/data')
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Data fetched:', data); // Log fetched data

        if (Array.isArray(data)) {
            data.forEach(item => {
                var marker = L.marker([item.latitude, item.longitude]);
                marker.date = item.date;
                marker.time = item.time;
                marker.title = item.title;
                marker.city = item.city;
                marker.message = item.message;
                marker.latitude = item.latitude;
                marker.longitude = item.longitude;
                marker.video = item.video;

                marker.bindPopup(`<b>${item.title}`);
                marker.on('click', function(e) {
                    updateSidebar(e.target);
                    updateBottomSidebar(e.target);
                });

                markers.addLayer(marker);
                leafletMarkers.push({marker: marker, text: item.title});
            });

            // Add marker cluster group to the map
            map.addLayer(markers);

            // Add search control (Leaflet Geocoder Control)
            var searchControl = L.Control.geocoder({
                defaultMarkGeocode: false,
                collapsed: true,
                placeholder: 'Search for a location...',
                geocoder: L.Control.Geocoder.nominatim(),
                position: 'topright'
            }).on('markgeocode', function(e) {
                var bbox = e.geocode.bbox;
                var markersBounds = L.latLngBounds([bbox.getSouthWest().lat, bbox.getSouthWest().lng], [bbox.getNorthEast().lat, bbox.getNorthEast().lng]);
                map.fitBounds(markersBounds);
            }).addTo(map);

            // Update marker count in sidebar when map zoom changes
            map.on('zoomend', function() {
                var currentZoom = map.getZoom();
                document.getElementById('marker-count').textContent = markers.getVisibleParentMarkers().length;
                document.getElementById('current-zoom').textContent = currentZoom;
            });

        } else {
            console.error('Response data is not an array:', data);
            // Handle the error or unexpected response here
        }
    })
    .catch(error => console.error('Error fetching data:', error)); // Log detailed error message
