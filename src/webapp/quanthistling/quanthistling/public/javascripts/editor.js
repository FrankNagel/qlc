YUI.add('quanthistling-editor', function(Y) {
 
    // Array Remove - By John Resig (MIT Licensed)
    Array.remove = function(array, from, to) {
        var rest = array.slice((to || from) + 1 || array.length);
        array.length = from < 0 ? array.length + from : from;
        return array.push.apply(array, rest);
    };

    Y.namespace('quanthistling');
 
    var Editor = function(config) {
        Editor.superclass.constructor.apply(this);
        var attributeConfig = {
            annotations : {},
            fulltext : {},
            annotationvalues: {},
            saveurl: {}
        };
        this.addAttrs(attributeConfig, config);
        this._updateFulltext();
        this._updateAnnotationValues();
        this._updateAnnotations();
        
        Y.on("click", this._buttonSetClicked, "#set-start-end", this);
        Y.on("click", this._buttonAddAnnotationClicked, "#buttons", this);
        Y.on("click", this._buttonEditOrDeleteAnnotationClicked, "#annotations", this);
        Y.on("click", this._buttonEditFulltextClicked, "#annotation-fulltext", this);
        Y.on("click", this._buttonPageClicked, "#pagebuttons", this);
        
        //Y.on('io:complete', _ioComplete, this);
    }
    
    Y.augment(Editor, Y.Attribute);
    
    Y.extend(Editor, Y.Base, {
        
        _updateAnnotations: function() {
            v = this.get("annotations");
            var annotations_html = "<tr><th>Type</th><th>Value</th><th>Start</th><th>End</th><th>Substring</th><th>Delete</th></tr>";
            for (i=0;i<v.length;i++) {
                var a = v[i];
                annotations_html += '<tr id="annotation-' + i + '"><td>' + a['annotationtype'] + '</td><td>' + a['value'] + '</td><td>' + a['start'] + '</td><td>' + a['end']  + '</td><td>' + a['string'] + '</td><td>'
                //annotations_html += '<button type="button" name="edit-annotation' + i + '" value="edit-annotation-' + i + '">Edit</button>';
                annotations_html += '<button type="button" name="delete-annotation' + i + '" value="delete-annotation-' + i + '">Delete</button>';
            }
            Y.get("#annotations").set("innerHTML", annotations_html);            
        },
        
        _updateAnnotationValues: function() {
            var v = this.get("annotationvalues");
            var buttons_html = "";
            for (i=0;i<v.length;i++) {
                var parts = v[i].split(".");
                buttons_html += '<button type="button" name="' + v[i] + '" value="' + v[i] + '">' + parts[1] + '</button>';
            }
            Y.get("#buttons").set("innerHTML", buttons_html);            
        },
        
        _updateFulltext: function() {
            Y.get("#fulltext").set("innerHTML", this.get("fulltext"));
        },
        
        _buttonSetClicked: function() {
            if (!this._hasSelection()) {
                alert("Your browser does not support selections. Please use another browser to use the Set-Button or enter values manually.")
                return;
            }
            var _range = this._getRange();
            var _sel = this._getSelection();
            if (_range) {
                Y.get("#annotation-start").set("value", _range.startOffset);
                Y.get("#annotation-end").set("value", _range.endOffset);
                Y.get("#annotation-string").set("value", _sel)
            } else {
                alert("Please select a range in the fulltext.")
            }
        },
        
        _buttonAddAnnotationClicked: function(e) {
            var _button = e.target.get("value");
            var _parts = _button.split(".");
            var _start = Y.get("#annotation-start").get("value");
            var _end = Y.get("#annotation-end").get("value");
            var _string = Y.get("#annotation-string").get("value");
            var _current_annotations = this.get("annotations");
            _current_annotations.push({ start: _start, end: _end, annotationtype: _parts[0], value: _parts[1], string: _string });
            this.set("annotations", _current_annotations);
            this._updateAnnotations();
        },
        
        _buttonEditOrDeleteAnnotationClicked: function(e) {
            var _button = e.target.get("value");
            var _parts = _button.split("-");
            var _current_annotations = this.get("annotations");
            var _new_annotations = [];
            for (i=0;i<_current_annotations.length;i++) {
                if (i != _parts[2]) {
                    _new_annotations.push(_current_annotations[i]);
                }
            }
            this.set("annotations", _new_annotations);
            this._updateAnnotations();
        },
        
        _buttonEditFulltextClicked: function(e) {
            var _button = e.target.get("value");
            if (_button == "edit-fulltext") {
                Y.get("#p-input-fulltext").setStyle("display", "block");
            } else if (_button == "cancel-fulltext") {
                Y.get("#input-fulltext").set("value", this.get("fulltext"));
                Y.get("#p-input-fulltext").setStyle("display", "none");                
            } else if (_button == "apply-fulltext") {
                this.set("fulltext", Y.get("#input-fulltext").get("value"));
                Y.get("#p-input-fulltext").setStyle("display", "none");
                Y.get("#fulltext").set("innerHTML", this.get("fulltext"));
            }
        },
        
        _buttonPageClicked: function(e) {
            var _button = e.target.get("value");
            if (_button == "reset-page") {
                check = confirm("Reset now?");
                if (check == true)
                    window.location.reload();
            } else if (_button == "cancel-page") {
                check = confirm("Cancel and go back to entry's index page now?");
                if (check == true)
                    window.location = "index.html";
            } else if (_button == "save-page") {
                var _json_fulltext = Y.JSON.stringify(this.get("fulltext"));
                var _json_annotations = Y.JSON.stringify(this.get("annotations"));
                var _data  = Y.QueryString.stringify({'annotations': _json_annotations, 'fullentry': _json_fulltext});
                var uri = this.get("saveurl");
                var cfg, request;
                cfg = {
                    sync: true,
                    method: 'POST',
                    data: _data
                };
                request = Y.io(uri, cfg);
                if (request.status == 200) {
                    check = confirm("The entry was saved successfully. Do you want to go back to the entry's index page?");
                    if (check == true)
                        window.location = "index.html";
                } else {
                    alert('There was an error while saving: ' + request.statusText + ' (' + request.status + '). Please try again.');                    
                }
            }
        },

        /**
        * @private
        * @method _getDoc
        * @description Get the Document of the IFRAME
        * @return {Object}
        */
        _getDoc: function() {
            return document
        },
        
        /**
        * @private
        * @method _getWindow
        * @description Get the Window of the IFRAME
        * @return {Object}
        */
        _getWindow: function() {
            return window;
        },
        
        /**
        * @private
        * @method _hasSelection
        * @description Determines if there is a selection in the editor document.
        * @return {Boolean}
        */
        _hasSelection: function() {
            var sel = this._getSelection();
            var range = this._getRange();
            var hasSel = false;

            if (!sel || !range) {
                return hasSel;
            }

            //Internet Explorer
            if (Y.UA.ie || Y.UA.opera) {
                if (range.text) {
                    hasSel = true;
                }
                if (range.html) {
                    hasSel = true;
                }
            } else {
                if (Y.UA.webkit) {
                    if (sel+'' !== '') {
                        hasSel = true;
                    }
                } else {
                    if (sel && (sel.toString() !== '') && (sel !== undefined)) {
                        hasSel = true;
                    }
                }
            }
            return hasSel;
        },
        
        /**
        * @private
        * @method _getRange
        * @description Handles the different range objects across the A-Grade list.
        * @return {Object} Range Object
        */
        _getRange: function() {
            var sel = this._getSelection();

            if (sel === null) {
                return null;
            }

            if (Y.UA.webkit && !sel.getRangeAt) {
                var _range = this._getDoc().createRange();
                try {
                    _range.setStart(sel.anchorNode, sel.anchorOffset);
                    _range.setEnd(sel.focusNode, sel.focusOffset);
                } catch (e) {
                    _range = this._getWindow().getSelection()+'';
                }
                return _range;
            }

            if (Y.UA.ie || Y.UA.opera) {
                try {
                    return sel.createRange();
                } catch (e2) {
                    return null;
                }
            }

            if (sel.rangeCount > 0) {
                return sel.getRangeAt(0);
            }
            return null;
        },

        /**
        * @private
        * @method _getSelection
        * @description Handles the different selection objects across the A-Grade list.
        * @return {Object} Selection Object
        */
        _getSelection: function() {
            var _sel = null;
            if (this._getDoc() && this._getWindow()) {
                if (this._getDoc().selection) {
                    _sel = this._getDoc().selection;
                } else {
                    _sel = this._getWindow().getSelection();
                }
                //Handle Safari's lack of Selection Object
                if (Y.UA.webkit) {
                    if (_sel.baseNode) {
                            this._selection = {};
                            this._selection.baseNode = _sel.baseNode;
                            this._selection.baseOffset = _sel.baseOffset;
                            this._selection.extentNode = _sel.extentNode;
                            this._selection.extentOffset = _sel.extentOffset;
                    } else if (this._selection !== null) {
                        _sel = this._getWindow().getSelection();
                        _sel.setBaseAndExtent(
                            this._selection.baseNode,
                            this._selection.baseOffset,
                            this._selection.extentNode,
                            this._selection.extentOffset);
                        this._selection = null;
                    }
                }
            }
            return _sel;
        }

    });
    
    Y.quanthistling.Editor = Editor;
 
}, '0.0.1' /* module version */, {
    requires: ['base', 'node', 'event', 'attribute', 'json', 'io', 'querystring']
});