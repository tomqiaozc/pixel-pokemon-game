// billevent.js — Bill's House transformation event module

const BillEvent = (() => {
    let billState = null;

    async function loadState() {
        billState = await API.getBillState();
        return billState;
    }

    function getState() {
        return billState;
    }

    function isTransformed() {
        return billState && (billState.state === 'human' || billState.state === 'ticket_given');
    }

    function hasTicket() {
        return billState && billState.state === 'ticket_given';
    }

    async function startTransformation() {
        const result = await API.billTransform();
        if (result && result.success) {
            billState = { state: 'transforming' };
        }
        return result;
    }

    async function completeTransformation() {
        const result = await API.billComplete();
        if (result && result.success) {
            billState = { state: result.state || 'human' };
        }
        return result;
    }

    async function giveTicket() {
        const result = await API.billTicket();
        if (result && result.success) {
            billState = { state: 'ticket_given' };
        }
        return result;
    }

    function getBillDialogue() {
        if (!billState) return ['...'];
        switch (billState.state) {
            case 'pokemon':
                return [
                    'Help! I was experimenting with my Cell Separation System and got merged with a Pokemon!',
                    'Please run the Cell Separation System on my PC to change me back!',
                ];
            case 'transforming':
                return ['The machine is running... please wait!'];
            case 'human':
                return [
                    'I\'m back to normal! Thank you so much!',
                    'Here, take this S.S. Ticket as thanks!',
                    'It\'s for the luxury liner in Vermilion City. Enjoy!',
                ];
            case 'ticket_given':
                return [
                    'Thanks again for saving me!',
                    'Have fun on the S.S. Anne in Vermilion!',
                ];
            default:
                return ['...'];
        }
    }

    function renderTicketReceived(ctx, canvasW, canvasH) {
        ctx.fillStyle = 'rgba(0,0,0,0.7)';
        ctx.fillRect(0, 0, canvasW, canvasH);
        ctx.fillStyle = '#60b0e8';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Got an S.S. Ticket!', canvasW / 2, canvasH / 2 - 10);
        ctx.fillStyle = '#ffffff';
        ctx.font = '12px monospace';
        ctx.fillText('A ticket for the S.S. Anne.', canvasW / 2, canvasH / 2 + 10);
        ctx.textAlign = 'left';
    }

    return {
        loadState,
        getState,
        isTransformed,
        hasTicket,
        startTransformation,
        completeTransformation,
        giveTicket,
        getBillDialogue,
        renderTicketReceived,
    };
})();
