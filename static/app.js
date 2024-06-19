const recordButton = document.getElementById('recordButton');
const videoElement = document.getElementById('avatarVideo');
const startButton = document.getElementById('startButton');
const responseInput = document.getElementById('userResponse')
const label = document.getElementById("respuestas-label")
//const submitResponseButton = document.getElementById('submitResponseButton')
let userResponse = 0;
let id_pregunta = 0;
let mediaRecorder;
let audioChunks = [];
let greeting = true;
let respuestas = [];

function removeListener() {
    videoElement.removeEventListener('ended', handleVideoEnded);
    console.log('Programa finalizado');
}

videoElement.addEventListener('ended', handleVideoEnded);

async function handleVideoEnded() {
    if(greeting == false){
        if(id_pregunta == 4){
            const respuesta = await fetch("/speech_to_text");
            const { text } = await respuesta.json();
            respuestas.push(text)
            //const { respuestas } = await fetch("/get_response");
            label.innerText = respuestas.join("\n");
            const finalVideo = await fetch("/final_talk");
            const { video_url } = await finalVideo.json();
            console.log(video_url)
        // Reproducir el próximo video
            playVideoSegment(video_url);
            removeListener()
        }
        if(id_pregunta < 4){

        const respuesta = await fetch("/speech_to_text");
        const { text } = await respuesta.json();

        const nextVideo= await fetch('/generate_talk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id_pregunta: id_pregunta })
        });
        const { video_url } = await nextVideo.json();
        console.log(video_url)

        // Reproducir el próximo video
        playVideoSegment(video_url);
        
        respuestas.push(text)
        id_pregunta++;}}
    else{
        const nextVideo= await fetch('/generate_talk', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id_pregunta: id_pregunta })
        });
        const { video_url } = await nextVideo.json();
        console.log(video_url);

        // Reproducir el próximo video
        playVideoSegment(video_url);
        id_pregunta++;
        greeting = false;
    }
}

//responseInput.addEventListener('change', async function() {
//    // Obtener la respuesta del usuario
//    // Hacer una solicitud al servidor para obtener el próximo video y guardar la respuesta
//    const nextVideoResponse = await fetch('/generate_talk', {
//        method: 'POST',
//        headers: {
//            'Content-Type': 'application/json'
//        },
//        body: JSON.stringify({ response: userResponse })
//    });
//    const { video_url } = await nextVideoResponse.json();
//    console.log(video_url)
//    
//    // Reproducir el próximo video
//    playVideoSegment(video_url);
//});

startButton.addEventListener('click', async function() {
    // Fetch para obtener la URL del video desde el endpoint
    const response = await fetch('/initial-greeting');
    const { video_url } = await response.json();
    
    // Llamamos a la función para reproducir el video con la URL obtenida
    playVideoSegment(video_url);
});


function playVideoSegment(url) {
    videoElement.addEventListener('started', () => {
        console.log('Video started');
        // Show response input when video ends
        startDiv.style.display = 'none';
    }, { once: true });


        videoElement.src = url;
        videoElement.load();
        videoElement.play().then(_ => {
            console.log('Video is playing');
        }).catch(e => {
            console.error('Error playing video:', e);
        });
    
        // Event listener for video end
        videoElement.addEventListener('ended', () => {
            console.log('Video ended');
            // Show response input when video ends
        });
    }

// Initialize the video element with an initial greeting or prompt
async function init() {
    //await fetch('/');
    const response = await fetch('/initial-greeting');
    const { video_url } = await response.json();
    
    playVideoSegment(video_url);
}

//init();
