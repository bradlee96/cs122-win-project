function getSummoner() {
    var summonerName = document.summonersearch.summoner.value;
    location.href = "?summoner=" + summonerName;
};

function goToChampionSelect() {
    location.href = "/championselect";
};

function retrieveSummoner() {
    location.href = "?getsummoner=True";
    var button = document.getElementById("getSummoner");
    button.disabled = true;
    button.value = "Loading... Please do not refresh the page.";
};
