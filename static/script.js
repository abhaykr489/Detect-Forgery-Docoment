$(document).ready(function(){
    var isProcessing = false; // Flag to prevent multiple submissions
    var loadingSpinner = $('.loading-spinner'); // Reference to the loading spinner element
    $('#uploadForm').submit(function(event){
        event.preventDefault();

        if (isProcessing) {
            return;
        }

        isProcessing = true;  // Set the flag to true to indicate processing
        $('#submitBtn').prop('disabled', true);
          // Show the loading spinner when the form is submitted
        loadingSpinner.show();

        var formData = new FormData($('#uploadForm')[0]);

        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response){
                 // Clear existing error message
                 $('#result').html('');
                if (response.error) {
                    document.getElementById("detail").innerHTML = "invalid / torn image detected!";
                    var errorMessage = (response.responseJSON && response.responseJSON.error) ? response.responseJSON.error : 'Unknown error occurred.';
                    $('#result').html('<p class="error">Error: ' + errorMessage + '</p>');
                    // Display the error message inside the canvas
                    var c = document.getElementById("canv2");
                    var ctx = c.getContext("2d");
                    ctx.font = "30px Arial";
                    ctx.strokeText("invalid or torn image found. Please upload valid image", 10, 50);
                } else {

                     if(response.forgery_image_path){
                     // display forgery data
                     $('#forgeryInfo').html('<p class="success">Forgery detected successfully.' + '<p>Forgery Percentage: ' + response.forgery_percentage.toFixed(2) + '%</p>');
                     $('#forgeryInfo').append('<p>Forgery Types: ' + response.forgery_type + '</p>');

                    //display forgery image
                     document.getElementById("detail").innerHTML = "forgery marked image!";
                     const canvas = document.getElementById("canv1");
                     const ctx = canvas.getContext("2d");
                     const imageUrl = response.forgery_image_path;
                     // Replace with the actual URL
                     const img = new Image();
                     img.src = imageUrl;
                    img.onload = function() {
                        // Set canvas dimensions to match the image
                        canvas.width = img.width;
                        canvas.height = img.height;

                        // Draw the image onto the canvas without losing quality
                        ctx.drawImage(img, 0, 0, img.width, img.height);
                    };
                   }
                }
                isProcessing = false;
                $('#submitBtn').prop('disabled', false); // Re-enable the submit button
                loadingSpinner.hide(); // hide spinner
            },
            error: function(error){
                var errorMessage = (error.responseJSON && error.responseJSON.error) ? error.responseJSON.error : 'Unknown error occurred.';
                $('#result').html('<p class="error">Error: ' + errorMessage + '</p>');
                isProcessing = false;
                $('#submitBtn').prop('disabled', false); // Re-enable the submit button
                loadingSpinner.hide();
            }
        });

        return false;
    });
});

function upload(){
  // Clear canvases
    var canvas1 = document.getElementById("canv1");
    var ctx1 = canvas1.getContext("2d");
    ctx1.clearRect(0, 0, canvas1.width, canvas1.height);

    var fileinput = document.getElementById("fileInput");
    var image = new SimpleImage(fileinput);
    image.drawTo(canvas1);
}


