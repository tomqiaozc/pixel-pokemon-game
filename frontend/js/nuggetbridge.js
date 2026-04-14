// nuggetbridge.js — Nugget Bridge gauntlet tracking and reward module

const NuggetBridge = (() => {
    let bridgeState = null;

    async function loadState() {
        bridgeState = await API.getNuggetBridgeState();
        return bridgeState;
    }

    function getState() {
        return bridgeState;
    }

    async function onTrainerDefeated(trainerIndex) {
        const result = await API.defeatBridgeTrainer(trainerIndex);
        if (result) bridgeState = result;
        return result;
    }

    async function tryAwardNugget() {
        if (!bridgeState || bridgeState.trainers_defeated < 5) return null;
        if (bridgeState.nugget_awarded) return null;
        const result = await API.awardNugget();
        if (result && result.success) {
            bridgeState.nugget_awarded = true;
        }
        return result;
    }

    function isBridgeClear() {
        return bridgeState && bridgeState.bridge_clear;
    }

    function renderBridgeProgress(ctx, x, y) {
        if (!bridgeState) return;
        const defeated = bridgeState.trainers_defeated || 0;
        ctx.fillStyle = '#ffffff';
        ctx.font = '10px monospace';
        ctx.fillText(`Bridge: ${defeated}/5`, x, y);
    }

    function renderNuggetReceived(ctx, canvasW, canvasH) {
        ctx.fillStyle = 'rgba(0,0,0,0.7)';
        ctx.fillRect(0, 0, canvasW, canvasH);
        ctx.fillStyle = '#ffd700';
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Got a Nugget!', canvasW / 2, canvasH / 2 - 10);
        ctx.fillStyle = '#ffffff';
        ctx.font = '12px monospace';
        ctx.fillText('A nugget of pure gold!', canvasW / 2, canvasH / 2 + 10);
        ctx.textAlign = 'left';
    }

    return {
        loadState,
        getState,
        onTrainerDefeated,
        tryAwardNugget,
        isBridgeClear,
        renderBridgeProgress,
        renderNuggetReceived,
    };
})();
