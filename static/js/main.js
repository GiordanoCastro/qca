// Scripts del Sistema de Reservas de Laboratorios de Química

document.addEventListener('DOMContentLoaded', () => {
    // Inicializar iconos de Lucide
    if (window.lucide) {
        window.lucide.createIcons();
    }

    // Validación interactiva de horas 08:30 a 18:30 en el cliente
    const inputIni = document.getElementById('hora_inicio');
    const inputFin = document.getElementById('hora_fin');
    const formReserva = document.getElementById('form-reserva');

    function aMinutos(hStr) {
        if (!hStr) return null;
        const [h, m] = hStr.split(':').map(Number);
        return h * 60 + m;
    }

    if (inputIni && inputFin) {
        const MIN_OPERATIVO = 8 * 60 + 30;  // 08:30
        const MAX_OPERATIVO = 18 * 60 + 30; // 18:30

        function validarHoras() {
            const mIni = aMinutos(inputIni.value);
            const mFin = aMinutos(inputFin.value);

            if (mIni !== null) {
                if (mIni < MIN_OPERATIVO) {
                    inputIni.setCustomValidity('El horario de laboratorio inicia a las 08:30 am.');
                } else if (mIni >= MAX_OPERATIVO) {
                    inputIni.setCustomValidity('La hora de inicio no puede ser posterior a las 18:30 hrs.');
                } else {
                    inputIni.setCustomValidity('');
                }
            }

            if (mFin !== null) {
                if (mFin > MAX_OPERATIVO) {
                    inputFin.setCustomValidity('El laboratorio cierra a las 18:30 hrs.');
                } else if (mIni !== null && mFin <= mIni) {
                    inputFin.setCustomValidity('La hora de término debe ser posterior a la hora de inicio.');
                } else {
                    inputFin.setCustomValidity('');
                }
            }
        }

        inputIni.addEventListener('change', validarHoras);
        inputFin.addEventListener('change', validarHoras);
    }
});
