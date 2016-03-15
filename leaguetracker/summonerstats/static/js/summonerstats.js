// ORIGINAL
// Redirects to summoner (or summonernotfound) view
function getSummoner() {
    var summonerName = document.summonersearch.summoner.value;
    location.href = "?summoner=" + summonerName;
};

// Redirects to championselect view
function goToChampionSelect() {
    location.href = "/championselect";
};

// Adds GET request so that page knows to run python script and disables button
// so that user cannot press more than once
function retrieveSummoner() {
    location.href = "?getsummoner=True";
    var button = document.getElementById("getSummoner");
    button.disabled = true;
    button.value = "Loading... Please do not refresh the page.";
};
