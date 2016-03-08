function getSummoner() {
    var summonerName = document.summonersearch.summoner.value;
    location.href = "?summoner=" + summonerName;
};

function goToChampionSelect() {
    location.href = "/championselect";
};
