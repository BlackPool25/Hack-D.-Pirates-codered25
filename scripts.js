// Constants
const WEATHER_API_KEY = 'your_openweather_api_key_here';
const BANGALORE_COORDS = { lat: 12.9416, lng: 77.5668 };

// Elements
const profileButton = document.getElementById('profile');
const userProfileItem = document.getElementById('user-profile');
const loginModal = document.getElementById('loginModal');
const loginForm = document.getElementById('loginForm');

// Show Login Modal
function openLoginPage() {
    loginModal.classList.remove('hidden'); // Show the modal
}

// Hide Login Modal
function closeLoginPage(event) {
    if (event.target === loginModal) {
        loginModal.classList.add('hidden'); // Hide the modal
    }
}

// Attach Event Listeners
profileButton.addEventListener('click', openLoginPage);
userProfileItem.addEventListener('click', openLoginPage);
loginModal.addEventListener('click', closeLoginPage);

// Form Submission
loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('https://your-backend-url/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });

        if (response.ok) {
            alert('Login successful!');
            loginModal.classList.add('hidden');
        } else {
            alert('Login failed. Please check your credentials.');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while logging in.');
    }
});

// Fetch Temperature
async function fetchTemperature() {
    try {
        const response = await fetch(
            `https://api.openweathermap.org/data/2.5/weather?q=Bangalore&appid=${WEATHER_API_KEY}&units=metric`
        );
        const data = await response.json();
        document.getElementById('temperature').innerText = `${data.main.temp}°C`;
    } catch (error) {
        console.error('Error fetching temperature:', error);
    }
}

// Initialize Google Maps
function initGoogleMap() {
    const map = new google.maps.Map(document.getElementById('map'), {
        center: BANGALORE_COORDS,
        zoom: 13,
    });

    const locateMeButton = document.createElement('button');
    locateMeButton.textContent = 'Locate Me';
    locateMeButton.classList.add('locate-me-button');

    locateMeButton.onclick = () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const userLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                    };
                    new google.maps.Marker({
                        position: userLocation,
                        map: map,
                        title: 'You are here!',
                    });
                    map.setCenter(userLocation);
                },
                () => alert('Unable to fetch location. Please try again.')
            );
        } else {
            alert('Geolocation is not supported by your browser.');
        }
    };

    map.controls[google.maps.ControlPosition.TOP_RIGHT].push(locateMeButton);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    fetchTemperature();
});
