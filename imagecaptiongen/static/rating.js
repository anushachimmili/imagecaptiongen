$(document).ready(function() {
    const ratingContainers = [...document.getElementsByClassName("rating")];

    ratingContainers.forEach(container => {
        const imgId = container.id.slice(6);  // get the img_id from the id of the container
        const ratingStars = [...container.getElementsByClassName("rating__star")];
        executeRating(ratingStars, imgId);
    });

    function executeRating(stars, imgId) {
        const starClassActive = "rating__star fa fa-star";
        const starClassInactive = "rating__star fa fa-star-o";
        const starsLength = stars.length;
        stars.forEach((star, i) => {  // use forEach instead of map
            star.onclick = (function(i) {  // use a closure to capture the current index
                return function() {
                    const rating = i + 1;

                    if (star.className === starClassInactive) {
                        $.ajax({
                            url: '/caption/rate/' + imgId + '/' + rating,  // replace with your server endpoint
                            type: 'POST',
                            data: {
                                img_id: imgId,
                                rating: rating
                            },
                            success: function(response) {
                                if(response.status === 'success') {
                                    stars.forEach((star, i) => {
                                        star.className = i < rating ? "rating__star fa fa-star" : "rating__star fa fa-star-o";
                                    });
                                }
                            },
                            error: function(jqXHR, textStatus, errorThrown) {
                                console.error("AJAX request failed: ", textStatus, errorThrown);
                            }
                        });
                    }
                }
            })(i);
        });
    }
});