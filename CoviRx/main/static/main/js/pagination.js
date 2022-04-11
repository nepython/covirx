var currentPage;
$('.nav-link')[4].classList.add('active'); // highlights the References nav item
var els = $("tr").not(":first"), grp = 5, cnt = Math.ceil(els.length/grp), ind = 0;
for(var i = 1; i <= cnt;i++) {
    els.slice(ind, ind += grp).addClass(`page ${i}`);
    $(`<a id="link-${i}" onclick="changePage('${i}')" href="#">${i}</a>`).insertBefore('.pagination #link-next');
}
changePage(1);
function changePage(pageNumber) {
    if (pageNumber=='-1') pageNumber = Math.max(currentPage-1, 1);
    else if (pageNumber=='-2') pageNumber = Math.min(currentPage+1, cnt);
    $('.page').hide();
    $(`.pagination a#link-${currentPage}`).removeClass('active');
    $(`.page.${pageNumber}`).show();
    $(`.pagination a#link-${pageNumber}`).addClass('active');
    currentPage = pageNumber;
}
