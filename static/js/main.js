
var txtFilenames = data.txtFilenames;

document.addEventListener("DOMContentLoaded", function() {
    var images = document.querySelectorAll("#image-gallery img");
    var selectedImageContainer = document.querySelector("#selected-image");
    var itemList = document.querySelector("#item-list");
    var saveButton = document.getElementById("btn-save");

    function writeFile() {
        var selectedImage = document.querySelector("#image-gallery img.selected");
        
        // Check if an image is selected
        if (selectedImage) {
            // Get the new content of the .txt file
            var newContent = Array.from(itemList.querySelectorAll('.editable-field')).map(function(field) {
                return field.value;
            }).join(',');

            // Send a request to update the .txt file
            var txtFilename = selectedImage.getAttribute('data-txt-filename');
            fetch('/update-file/' + txtFilename, {
                method: 'POST',
                headers: {
                    'Content-Type': 'text/plain'
                },
                body: newContent
            });
        }
    }

    saveButton.addEventListener("click", function() {
        writeFile();
        fetch('/save', {
            method: 'POST',
        });
    });

    images.forEach(function(image) {
        image.addEventListener("click", function() {
            writeFile();

            images.forEach(function(img) {
                img.classList.remove("selected");
            });

            image.classList.add("selected");

            selectedImageContainer.innerHTML = '';
            var img = document.createElement("img");
            img.src = image.src;
            selectedImageContainer.appendChild(img);

            // Fetch the text file corresponding to the clicked image
            var txtFilename = image.getAttribute('data-txt-filename');
            fetch('/file/' + txtFilename)
                .then(response => response.text())
                .then(text => {
                    updateItemList(text);
                });
        });
    });

    // Process each text file
    txtFilenames.forEach(function(txtFilename) {
        fetch('/file/' + txtFilename)
            .then(response => response.text())
            .then(text => {
                updateItemList(text);
            });
    });


    function initializeAutocomplete(selector) {
        $(selector).autocomplete({
            source: function(request, response) {
                $.ajax({
                    url: "/autocomplete",
                    data: { q: request.term },
                    success: function(data) {
                        response(data);
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        console.log("AJAX error:", textStatus);
                    }
                });
            }
        });
    }

    function attachFocusBlurEvents(field, itemDiv) {
        $(field).focus(function() {
            itemList.currentField = field;
            $('#edit-item-field').val(field.value);
            updateModalPosition(itemDiv);
            $('#modalEditPopup').modal('show');
        });

        $(field).blur(function() {
            setTimeout(() => {
                if (itemList.currentField !== field) {
                    return;
                }

                itemList.currentField = null;
                $('#modalEditPopup').modal('hide');

                writeFile();
            }, 200); // delay in milliseconds
        });
    }


    function createEditableField(item) {
        var itemDiv = document.createElement("div");
        var field = document.createElement("input");
        field.type = "text";
        field.className = "editable-field";
        field.value = item;
        itemDiv.appendChild(field);

        // Attach focus and blur events to the field
        attachFocusBlurEvents(field, itemDiv);

        return itemDiv;
    }

    function updateModalPosition(itemDiv) {
        var itemPos = $(itemDiv).offset();
        var itemWidth = $(itemDiv).outerWidth();
        $('#modalEditPopup').css('top', itemPos.top + 'px');
        $('#modalEditPopup').css('left', (itemPos.left + itemWidth + 1) + 'px');
    }

    function updateItemList(csvContent) {
        var itemList = document.querySelector("#item-list");
        itemList.innerHTML = '';
        var items = csvContent.split(',').map(function(item) {
            return item.trim();
        });

        items.forEach(function(item) {
            var itemDiv = createEditableField(item);
            itemList.appendChild(itemDiv);
        });

        // Initialize autocomplete for the new fields
        initializeAutocomplete(".editable-field");
    }

    $('#btn-new').click(function() {
        var itemDiv = createEditableField('');
        if(itemList.currentField) {
            itemList.insertBefore(itemDiv, itemList.currentField.parentElement.nextSibling);
        } else {
            itemList.appendChild(itemDiv);
        }

        // Initialize autocomplete for the new field
        initializeAutocomplete(itemDiv.querySelector(".editable-field"));
    });

    $(document).on('click', '#btn-remove', function() {
        if(itemList.currentField) {
            itemList.currentField.parentElement.remove();
        } else {
            console.log("itemList.currentField is null");
        }
    });

    $('#modalEditPopup').on('show.bs.modal', function (e) {
        if (itemList.currentField) {
            updateModalPosition(itemList.currentField.parentElement);
        }
    });

});