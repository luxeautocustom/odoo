/** @odoo-module **/

import publicWidget from "web.public.widget";
import animations from "website.content.snippets.animation";

const paddingStep = 8;

/*
    The method to make title as url anchor
        * https://stackoverflow.com/questions/1053902/how-to-convert-a-title-to-a-url-slug-in-jquery        
*/
function convertToSlug(articleHeader) {
    return articleHeader
        .toLowerCase()
        .replace(/[^\w ]+/g,'')
        .replace(/ +/g,'-')
        ;        
};

/*
    The method to сalculate absolute top position
        * for unclear reasons offset().top returns window-relative top inside the widget
        * the same is true for getBoundingClientRect()
        * https://stackoverflow.com/questions/1480133/how-can-i-get-an-objects-absolute-position-on-the-page-in-javascript       
*/
function getTopPosition(elementQuery) {
    var top = 0,
        element = false;
    if (elementQuery.length != 0) {element = elementQuery[0]; };
    do {
        top += element.offsetTop  || 0;
        element = element.offsetParent;
    } while(element);
    return top
};
/*
     Documentation sections overview widget
*/
publicWidget.registry.docSectionPreview = publicWidget.Widget.extend({
    selector: '#doc_sections_content',
    events: {"click .doc_section_short": "_onOpenDocumentation",},
    _onOpenDocumentation: function (event) {
        event.preventDefault();
        event.stopPropagation();            
        window.open(event.currentTarget.id, "_self"); 
    },
});
/*
     Documentation page widget
*/
publicWidget.registry.docNavigation = animations.Animation.extend({
    selector: '#documentation_main_container',
    events: {
        "click .anchor_entry": "_onNavLinkClick",
        "click #hide_docu_navigation": "_onHideNavigationPanel",
        "click #scroll_top": "_onScrollTop",
        "click #docu_do_search": "_onSearch",
        "keyup #docu_search_key": "_onKeySearch",
        "click #clear_docu_search": "_onDocuClearSearch",
        "click #next_docu_search": "_onNextSearchResult",
        "click #previous_docu_search": "_onPreviousSearchResult",
    },
    effects: [{
        startEvents: 'scroll',
        update: '_updateScroll',
    }, {
        startEvents: 'resize',
        update: '_updateResize',
    }],
    /*
        Re-write to arrange table of contents, add article header anchors, calculate scrolling measures
    */
    start: function () {
        var self = this,
            navbarDiv = this.$("#nav_sticky");              
        this._defineMainElements(navbarDiv);
        this._generateAnchors(navbarDiv).then(function () {
            self._generateToc(navbarDiv).then(function () {
                self._simulateScrollOnOpen();
            })
        });
        return this._super.apply(this, arguments);
    }, 
    /*
        The method to parse all articles headers and anchors for that headers
    */
    _generateAnchors: function(navbarDiv) {
        var allArticles = this.$("#documentation_content .article_content_section"),
            allHeadersParsed = $.Deferred();
        if (allArticles && allArticles.length != 0) {
            var self = this,
                uniqueNum = 0;
            _.each(allArticles, function (article) {
                uniqueNum ++;
                var maxLevelElem = self.$("#nav_header_depth");
                if (maxLevelElem && maxLevelElem.length > 0) {
                    self.maxLevel = maxLevelElem[0].innerHTML;
                };
                self._addArticleAnchors(article, uniqueNum).then(function (toc) {
                    if (navbarDiv && navbarDiv.length) {
                        var articleID = article.id.toString();
                        var articleEntry = self.$("#article_entry_"+articleID);
                        if (articleEntry && articleEntry.length) {
                            articleEntry.after(toc)
                        };
                    };
                });
                if (uniqueNum == allArticles.length) {allHeadersParsed.resolve()};
            });                
        }
        else {
            allHeadersParsed.resolve();
        }
        return allHeadersParsed;
    },
    /* 
        The method to go through article content and add anchors to headers
            * The method returns the object with all headers relate to this article
            * In case order of headers in toc is not correct: 
            * >> https://stackoverflow.com/questions/497418/produce-heading-hierarchy-as-ordered-list
    */
    _addArticleAnchors: function (article, uniqueNum) {
        var finalDef = $.Deferred();                
        var toc = "";
        if (this.maxLevel) {   
            // Find all headers by query > adapt each + construct the toc
            var allHeaders = article.querySelectorAll("#documentation_content "+this.maxLevel);
            if (allHeaders && allHeaders.length != 0) {
                var activeLevel = 0,
                    itera = 0,
                    lastLevel = 0,
                    articleID = article.id.toString(),
                    ParentHeaders = {},
                    parentPadding = 0,
                    parentHeader = article.getAttribute("hrefid");
                ParentHeaders["0"] = {"parentHeader": parentHeader, "padding": parentPadding};
                _.each(allHeaders, function (articleHeader) {
                    itera ++;
                    var activeLevel = parseInt(articleHeader.tagName.substring(1));
                    var activeText = articleHeader.innerText;
                    if (activeText.length > 152) {
                        activeText = activeText.substring(0,150) + "...";
                    };
                    var titleSubString = convertToSlug(activeText).substring(0,30);
                    if (! titleSubString || titleSubString.replace("-", "") == "") {
                        // for the case it is not in Latin characters
                        titleSubString = "navheader";
                    };
                    var articleHeaderLink = titleSubString + "-" + articleID + "-" 
                                           + itera.toString() + "-" + uniqueNum; 
                    articleHeader.setAttribute("id", articleHeaderLink);
                    articleHeader.setAttribute("actheader", "1");
                    if (activeLevel > lastLevel) {
                        // the next level: h1 > h2, but also h1 > h5
                        toc += (new Array(activeLevel-lastLevel+1)).join("<ul>");
                        var parentHeaderSet = ParentHeaders[lastLevel.toString()];
                        parentHeader = parentHeaderSet.parentHeader;
                        parentPadding = parentHeaderSet.padding + paddingStep;
                        ParentHeaders[activeLevel.toString()] = {
                            "parentHeader": articleHeaderLink,
                            "padding": parentPadding,
                        };
                    }
                    else if (activeLevel < lastLevel) {
                        // the previous level: h2 > h1, but also h5 > h1
                        toc += (new Array(lastLevel-activeLevel+1)).join("</ul>");                           
                        var minLevel = lastLevel;
                        var levelFine = false;
                        while (!levelFine && minLevel >= 0) {
                            if (ParentHeaders[minLevel.toString()]) {
                                if (minLevel >= activeLevel) {
                                    delete ParentHeaders[minLevel.toString()];
                                }
                                else {
                                    var parentHeaderSet = ParentHeaders[minLevel.toString()];
                                    parentHeader = parentHeaderSet.parentHeader;
                                    parentPadding = parentHeaderSet.padding + paddingStep;
                                    levelFine = true;
                                }
                            }
                            minLevel --;
                        };
                        ParentHeaders[activeLevel.toString()] = {
                            "parentHeader": articleHeaderLink,
                            "padding": parentPadding
                        };
                    };
                    toc += "<li class='docu_nav_li' parent_id='#"+ parentHeader + "' style='margin-left: "
                            + parentPadding + "px !important;'><a href='#" + articleHeaderLink 
                            + "' class='anchor_entry'>" + activeText + "</a></li>";
                    lastLevel = activeLevel;
                    if (itera == allHeaders.length) {
                        toc += (new Array(activeLevel + 1)).join("</ul>");
                        finalDef.resolve(toc);
                    };
                });  
            }
            else {
                finalDef.resolve(toc);
            }             
        }
        else {
            finalDef.resolve(toc);
        };
        return finalDef
    },
    /*
        The method to prepare table of contents with proper ids according to article anchors
    */
    _generateToc: function(navbarDiv) {
        var readyForScroll = $.Deferred();
        if (navbarDiv && navbarDiv.length) {
            var self = this,
                allNavLinks = self.$(".anchor_entry"),
                navBarIcons = '<div class="nav_collapse_icons pull-right"> \
                                    <i class="fa fa-chevron-up nav_anchor_icon nav_anchor_collapse"></i> \
                                    <i class="fa fa-chevron-down nav_anchor_icon nav_anchor_expand"></i> \
                               </div>',
                kitera = 0;
            _.each(allNavLinks, function (navLink) {
                var aHref = navLink.getAttribute("href");
                var childIds = self.$("[parent_id='" + aHref +"']");
                if (childIds && childIds.length) {
                    var aElement = self.$("a[href='" + aHref +"']"); 
                    aElement.prepend(navBarIcons);
                };
                kitera ++;
                if (kitera == allNavLinks.length) {
                    readyForScroll.resolve();
                }
            });              
            this._defineNavElements(navbarDiv);
        }
        else {readyForScroll.resolve()};
        return readyForScroll;
    },
    /*
        Simulate scrolling at the first load to a proper anchor
         * we firstly go to the top to make sure scrolling event happens
    */
    _simulateScrollOnOpen: function() {        
        var self = this;
        this.safeContent = this.$("#documentation_content")[0].innerHTML.replace(/&nbsp;/g,'<span> </span>');
        var url = window.location.hash, idx = url.indexOf("#");
        var urlAnchor = idx != -1 ? url.substring(idx+1) : "";
        $("html,body").animate({scrollTop: 1}, 100, function () {
            if (urlAnchor) {self._onAnchorNavigate("#"+urlAnchor)};             
        });
    },       
    /*
        The method to define actual anchor offset
        Anchor offset is the editor menu height + affixed menu height + search bar height (if elements are present)
    */
    _defineAnchorOffset: function(scroll) {
        this.anchorOffset = getTopPosition($("#wrapwrap"));       
        if ($("header.o_header_affixed").length != 0 && $("header.o_header_affixed").hasClass("o_header_is_scrolled")) {
            this.anchorOffset = this.anchorOffset + $("header.o_header_affixed").outerHeight();
        };
        if (this.stickySearchBar) {this.anchorOffset = this.anchorOffset + this.stickySearchBarHeight};
        this.windowScrollTop = scroll;
    },
    /*
        The method calculate important for scrolling parameters (which are then are not changed but used for calcs)
        Needed for all scenarios
    */
    _defineMainElements: function(navbarDiv) {
        var searchBarSection = this.$("#docu_searchbar_section");
        this.safeContent = this.$("#documentation_content")[0].innerHTML.replace(/&nbsp;/g,'<span> </span>');
        this.activeSearchKey = -1;
        if (searchBarSection && searchBarSection.length) {
            this.stickySearchBarHeight = searchBarSection.outerHeight();
            this.stickySearchBar = searchBarSection;
            this.stickySearchBarTop = getTopPosition(searchBarSection);
            this.documentationContentHeight = this.$("#documentation_content")[0].offsetHeight;
        };
        this._defineAnchorOffset(0);

    },
    /*
        The method calculate important for scrolling parameters (which are then are not changed but used for calcs)
        Needed for scenarios when navbar exists
    */
    _defineNavElements: function(navbarDiv) {
        this.stickyNavigation = navbarDiv;
        this.documentationContentHeight = self.$("#documentation_content")[0].offsetHeight;
        this.stickyNavigationTop = getTopPosition(navbarDiv);
        this.scrollTopIcon = self.$("#scroll_top");
        this.windowHeight = $(window).height();
        this.documentHeight = $(document).height();
    },
    /*
        The method triggered when window is scrolled
    */
    _updateScroll: function (scroll) {
        var self = this;
        clearTimeout(this.scrollDebounceTimer);
        this.scrollDebounceTimer= setTimeout(function(){
            self._defineAnchorOffset(scroll);
            if (self.stickySearchBar) {self._stickSearchBar(scroll)};
            if (self.stickyNavigation) {
                self._stickToc(scroll);
                self._activateCurrentHeader(scroll);
            };
        }, 10);
    },
    /*
        The method triggered when window is resized
    */
    _updateResize: function () {
        var self = this;
        var searchBarSection = self.$("#docu_searchbar_section");
        this.windowHeight = $(window).height();
        this.documentHeight = $(document).height();
        this.documentationContentHeight = this.$("#documentation_content")[0].offsetHeight;
        if (this.stickySearchBar) {
            this.stickySearchBarHeight = searchBarSection.outerHeight();
        };
        this.$el.trigger('odoo-transitionstart');
    }, 
    /*
        The method to scroll searchbar with scrolling the page 
    */
    _stickSearchBar: function(scrollTop) {
        var self = this;
        var scrollDifference = scrollTop - self.stickySearchBarTop + self.anchorOffset - self.stickySearchBarHeight;
        if (scrollDifference > 0 && scrollDifference < self.documentationContentHeight-100) {
            if (! self.stickySearchBar.hasClass("stickynavtop") || !self.stickySearchBar.top != self.anchorOffset-self.stickySearchBarHeight) {
                self.stickySearchBar.addClass("stickynavtop");
                self.stickySearchBar.animate({"top": self.anchorOffset-self.stickySearchBarHeight, "padding-right": 15,}, 10);
                // Not to change the elements top
                self.$el.animate({"margin-top": self.stickySearchBarHeight}, 10);
            };
        }
        else {
            if (self.stickySearchBar.hasClass("stickynavtop")) {
                self.stickySearchBar.removeClass("stickynavtop");
                self.stickySearchBar.animate({"top": 0, "padding-right": 0,}, 10);
                self.$el.animate({"margin-top": 0}, 10);
            };
        };
    },
    /*
        The method to scroll table of contents with scrolling the page 
    */
    _stickToc: function(scrollTop) {
        if (scrollTop > this.stickyNavigationTop + 50) {this.scrollTopIcon.removeClass("knowsystem_hidden");}
        else {this.scrollTopIcon.addClass("knowsystem_hidden");}
        var scrollDifference = scrollTop - this.stickyNavigationTop + this.anchorOffset;
        var maxHeight = this.windowHeight - this.anchorOffset; 
        if (scrollDifference + maxHeight > this.documentationContentHeight) {
            // not to significantly overscroll the bottom
            var documentOffset = scrollDifference  + maxHeight - this.documentationContentHeight;
            maxHeight = maxHeight - documentOffset;
            if (maxHeight < 200) {
                scrollDifference = scrollDifference - (200-maxHeight);                     
            };
        };
        if (scrollDifference < 0) {
            maxHeight = maxHeight + scrollDifference;
            scrollDifference = 0;
        };
        if (maxHeight < 200) {maxHeight = 200;};
        var scrollTop = scrollDifference.toString() + "px";
        var maxHeight = maxHeight.toString() + "px";
        this.stickyNavigation.animate({"margin-top": scrollTop, "max-height": maxHeight}, 10)
    }, 
    /*
        The mouse click event method to animate to anchor
    */
    _onNavLinkClick: function(event) {
        var targetAnchorHref = event.currentTarget.getAttribute("href");
        this._onAnchorNavigate(targetAnchorHref);
    },
    /*
        The method to animate to anchor
    */
    _onAnchorNavigate: function(targetAnchorHref) {
        var self = this;
        if (targetAnchorHref == "#scrollTop=0") {$("html,body").animate({scrollTop: 0}, 400)}
        else {
            try {
                var initialOffset = this.anchorOffset;
                var targetAnchor = $(targetAnchorHref);
                var topOffset = getTopPosition(targetAnchor) - this.anchorOffset;
                if (Math.abs(targetAnchor.offset().top - this.anchorOffset) < 5) {
                    // to similate scrolling in case of refresh
                    topOffset = topOffset + 2;
                };
                $("html,body").animate({scrollTop: topOffset}, 400, function () {
                    if (Math.abs(targetAnchor.offset().top - self.anchorOffset) > 5) {
                        // adapt position since affixed menu might be added
                        topOffset = getTopPosition(targetAnchor) - self.anchorOffset;
                        $("html,body").animate({scrollTop: topOffset}, 10);
                    };
                });
            }
            catch (e) {
                console.warn("Anchor is not found");
            };             
        };
    },
    /*
        The method to check current documentation section to higlight and expand related TOC element
            * getBoundingClientRect().top returns window offset
    */
    _activateCurrentHeader: function(scrollTop) {
        var closestHeaders = [],
            allHeaders = this.$("[actheader='1']"),
            top, bottom;
        if (closestHeaders.length == 0) {
            var max = - Number.MAX_VALUE;
            for (var i=0; i<allHeaders.length; i++) {
                top = allHeaders[i].getBoundingClientRect().top - this.anchorOffset - 2;
                if (top <= 0 && top > max) {
                    max = top;
                    closestHeaders = ["#" + allHeaders[i].getAttribute("id")];
                };
            };
        }
        this._onActivateEntry(closestHeaders);
    },    
    /*
        The method to activate / hide / show navbar links
    */
    _onActivateEntry: function(anchors) {
        var allLIs = this.$(".docu_nav_li");
        allLIs.removeClass("shown_nav_entry");
        allLIs.removeClass("active_entry");   
        var self = this;
        _.each(anchors, function (anchor) {         
            self._onActivateSingleEntry(anchor);        
        });
    },
    /*
        The recursive method to activate / deactivate anchorss
    */
    _onActivateSingleEntry: function(anchor) {
        var aElement = self.$("a[href='" + anchor +"']").parent();
        if (aElement && aElement.length) {
            aElement.addClass("active_entry");
            // Expand and activate parent recursively
            var parentAnchorKey = aElement[0].getAttribute("parent_id");
            this._onActivateSingleEntry(parentAnchorKey);
            // Expand children
            var childeLIs = self.$("[parent_id='" + anchor +"']");
            childeLIs.addClass("shown_nav_entry");
        };
    },
         
    /*
        The click event method to get back to the start of documentation
    */        
    _onScrollTop: function(event) {
        $("html,body").animate({scrollTop: this.stickyNavigationTop-this.anchorOffset}, 400);
    },
    /*
        The click event method to show / hide toc
    */
    _onHideNavigationPanel: function(event) {
        var navigationPanel = this.$("#documentation_navigation"),
            docuContent = this.$("#documentation_content"),
            ulNavigation = this.$("#navigation_ul"),
            hideIcon = this.$("#hide_docu_navigation");
        if (ulNavigation.hasClass("knowsystem_hidden")) {
            navigationPanel.removeClass("navigation-collapsed");
            navigationPanel.addClass("col-lg-3");
            docuContent.removeClass("documentation-full-view");
            docuContent.addClass("col-lg-9");
            ulNavigation.removeClass("knowsystem_hidden");
            hideIcon.removeClass("fa-indent");
            hideIcon.addClass("fa-dedent");  
        }
        else {
            navigationPanel.removeClass("col-lg-3");
            navigationPanel.addClass("navigation-collapsed");     
            docuContent.removeClass("col-lg-9");
            docuContent.addClass("documentation-full-view");
            ulNavigation.addClass("knowsystem_hidden");        
            hideIcon.removeClass("fa-dedent");
            hideIcon.addClass("fa-indent");   
        };
    },
    
    /*
        The keyboard enter event to start search
    */
    _onKeySearch: function(event) {
        event.preventDefault();
        event.stopPropagation();
        if (event.keyCode === 13) {this.$("#docu_do_search").click()};
    },
    /*
        The mouse click event to start search and highligh keys in content
    */
    _onSearch: function(event) {
        /*
            The method to apply search key with parsed xml (look at the py method to_xml in misc)
        */
        function adaptToSpecialSymbols(thisNodeText) {
            var map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
            };
            return thisNodeText.replace(/[&<>]/g, function(m) { return map[m]; });
        };
        /*
            The method to set unique search id for elements. Not actually used, but usefull for testing
        */
        async function setUniqueSearchId(allNodes) {
            var setIDiterator = 0;
            _.each(allNodes, function (node) {
                setIDiterator++;
                node.setAttribute("searchdocuid", setIDiterator)
            });
        };
        /*
            The method to search isnide substring
             * https://stackoverflow.com/questions/3410464/how-to-find-indices-of-all-occurrences-of-one-string-in-another-in-javascript
        */
        function searchMatchsNum(searchKey, searchText, caseSensitive) {
            var searchKeyLen = searchKey.length;
            if (searchKeyLen == 0) {return 0;};
            if (!caseSensitive) {
                searchKey = searchKey.toLowerCase();
                searchText = searchText.toLowerCase();
            };
            var startIndex = 0, 
                index,
                resultNum = 0;
            while ((index = searchText.indexOf(searchKey, startIndex)) > -1) {
                resultNum ++;
                startIndex = index + searchKeyLen;
            };
            return resultNum;
        };
        /*
            The method to add extra tag <docusearch> for all found nodes containing key
        */
        function wrapTextNode(node) {
            var newElementNode = document.createElement('docusearch');
            newElementNode.innerText = $(node).text();
            node.parentNode.replaceChild(newElementNode, node);
            return newElementNode;
        };
        /*
            The method to add highlight span for found matches
        */
        function replaceWithHighlight(node, regexPattern, caseSensitive, firstOccurence) {
            var regexFlags = "",
                notFirstClass = "";
            regexPattern = adaptToSpecialSymbols(regexPattern); // since innerHTML has those
            if (!firstOccurence) {
                // global replacement of all occrurences
                regexFlags = regexFlags + "g";
            }
            else if (firstOccurence == "last") {
                // the last occurence
                regexPattern = regexPattern + "$";
            }
            else if (firstOccurence == "first") {
                // The first occurenct
                notFirstClass = "docu_search_highlight_no_nav"
            };
            if (!caseSensitive) {
                // case insensitive
                regexFlags = regexFlags + "i";
            };
            regexPattern = new RegExp(regexPattern, regexFlags);
            node.innerHTML = node.innerHTML.replace(
                regexPattern, 
                function(match, contents, offset, input_string) {
                    return "<docusearch class='docu_search_highlight " + notFirstClass + "'>"+match+"</docusearch>";
                }
            );
        };
        /*
            The method to find out whether checked text starts with search key end
        */
        function findStartOverlap(searchKey, searchText) {
            var searchKeyLen = searchKey.length;
            if (searchKeyLen <= 0) {return ""};    
            if (searchText.startsWith(searchKey)) {return searchKey};
            searchKey = searchKey.slice(0, searchKeyLen-1);
            return findStartOverlap(searchKey, searchText)
        };
        /*
            The method to find out whether checked text end with with search key start
        */
        function findEndOverlap(searchKey, searchText) {
            var searchKeyLen = searchKey.length;
            if (searchKeyLen <= 0) {return ""};       
            if (searchText.endsWith(searchKey)) {return searchKey;};
            searchKey = searchKey.slice(0, searchKeyLen-1);
            return findEndOverlap(searchKey, searchText)
        };
        /*
            The method to retrieve search parts if they are in different text nodes
        */
        function searchKeyWordParts(nodes, searchKey, caseSensitive, tempNodes, tempSearch) {
            /*
                The method to retrieve search parts if they are in different text nodes
            */
            function highlighSearchParts(fNodes, fSearch) {
                var itera = 0;
                _.each(fNodes, function(node) {
                    var newElementNode = wrapTextNode(node);
                    var occurence = "first";
                    if (itera == 0) {
                        occurence = "last";
                    };
                    replaceWithHighlight(newElementNode, fSearch[itera], caseSensitive, occurence);
                    itera ++;
                });                    
            };
            _.each(nodes, async function (node) {
                var thisNodeText = $(node).text();
                if (thisNodeText) {
                    if (!caseSensitive) {
                        searchKey = searchKey.toLowerCase();
                        thisNodeText = thisNodeText.toLowerCase();
                    };
                    if (node.nodeType == 3) {
                        if (tempNodes.length == 0) {
                            var endOverLap = findEndOverlap(searchKey, thisNodeText);    
                            if (endOverLap) {
                                tempNodes.push(node);
                                tempSearch.push(endOverLap);
                            };                       
                        }
                        else {
                            var tempSearchKey = tempSearch.join("");
                            var searchKeyPart = searchKey.slice(tempSearchKey.length, searchKey.length);
                            var startOverlap = findStartOverlap(searchKeyPart, thisNodeText);
                            if (startOverlap) {
                                tempNodes.push(node);
                                tempSearch.push(startOverlap);  
                                tempSearchKey = tempSearch.join("");
                                if (searchKey.includes(tempSearchKey)) {
                                    if (tempSearchKey == searchKey) {
                                        await highlighSearchParts(tempNodes, tempSearch);
                                        tempNodes.length = 0;
                                        tempSearch.length = 0;
                                    }
                                    else {
                                        // the case A_Bxxx_C > search by ABC. Such string length should be the same
                                        if (startOverlap.length != thisNodeText.length) {
                                            tempNodes.length = 0;
                                            tempSearch.length = 0;
                                        }
                                    };
                                }
                                else {
                                    tempNodes.length = 0;
                                    tempSearch.length = 0;
                                };                             
                            }
                            else {
                                tempNodes.length = 0;
                                tempSearch.length = 0;
                            };
                        
                            if (tempNodes.length == 0) {
                                // check the last item for being start 
                                var endOverLap = findEndOverlap(searchKey, thisNodeText);    
                                if (endOverLap) {
                                    tempNodes.push(node);
                                    tempSearch.push(endOverLap);
                                };
                            };
                        };
                    }
                    else if (node.nodeType == 1) {
                        await searchKeyWordParts($(node).contents(), searchKey, caseSensitive, tempNodes, tempSearch);
                    };
                };
            });
        };
        /*
            The method to go over all elements recursively and replace with matches
        */
        async function findLastNodewithKey(nodes, searchKey, caseSensitive, lastMatch) {
            var totalNodesNum = 0;
            _.each(nodes, async function(node){
                var thisNodeMatches;
                if (node.nodeType == 1) {
                    // element node > need to check children
                    thisNodeMatches = searchMatchsNum(searchKey, $(node).text(), caseSensitive);
                    if (thisNodeMatches > 0) {
                        if ($(node).contents().length > 0) {
                            findLastNodewithKey($(node).contents(), searchKey, caseSensitive, thisNodeMatches).then(function (childNodeMatches) {
                                if (childNodeMatches[1] > childNodeMatches[0]) {
                                    /* the root element contains more matches than all children elements
                                       example: <strong>1</strong>2 when search by '12' */
                                    // $(node).addClass("docu_search_highlight"); - if to simply highlight parent el
                                    searchKeyWordParts($(node).contents(), searchKey, caseSensitive, [], [])
                                }
                            });
                        };
                    };
                }
                else if (node.nodeType == 3) {
                    // text node: if there are matches > firstly replace it with element nodes
                    thisNodeMatches = searchMatchsNum(searchKey, $(node).text(), caseSensitive);
                    if (thisNodeMatches > 0) {
                        var newElementNode = wrapTextNode(node);
                        replaceWithHighlight(newElementNode, searchKey, caseSensitive);
                    };
                }
                else {
                    // other node types are not checked at all
                    thisNodeMatches = 0;
                };
                totalNodesNum = totalNodesNum + thisNodeMatches;
            });
            return [totalNodesNum, lastMatch]
        };
        /*
            The search algorithm
        */            
        var self = this,
            firstLevelNodes,
            searchKey = self.$("#docu_search_key")[0].value,
            searchType = self.$(".docu_search_selection.active")[0].id,          
            docuContentsObject = self.$("#documentation_content"),
            caseSensitive = false;
        self.searchResults = [];
        self.searchIDs = [];
        self.activeSearchKey = -1;
        self.$("#docu_search_results").addClass("knowsystem_hidden");
        if (searchKey) {
            // restore previous search highlight
            docuContentsObject[0].innerHTML = self.safeContent; 
            if (searchType == "docu_search_headers") {
                // the case <h2><h3></h3></h2> is impossible
                firstLevelNodes = docuContentsObject.find("h1,h2,h3,h4,h5,h6");
            }
            else { 
                firstLevelNodes = docuContentsObject.contents();
                if (searchType == "docu_search_case_sensitive") {
                    caseSensitive = true;
                }
            }
            findLastNodewithKey(firstLevelNodes, searchKey, caseSensitive, 0).then(function (matchResults) {
                self.$("#docu_search_results").removeClass("knowsystem_hidden");
                var searchMatches = matchResults[0];
                self.$("#search_matches_num")[0].innerHTML = searchMatches;
                var allSearchPositions = self.$(".docu_search_highlight:not(.docu_search_highlight_no_nav)"),
                    uniqueHiglightId = 0,
                    SUID;
                _.each(allSearchPositions, function(node) {
                    uniqueHiglightId ++;
                    SUID = "seachkey_" +uniqueHiglightId.toString();
                    node.setAttribute("id", SUID);
                    self.searchResults.push(getTopPosition($(node)));
                    self.searchIDs.push(SUID);
                    if (uniqueHiglightId == allSearchPositions.length) {
                        self.$("#next_docu_search").click();
                    };
                });
                if (searchMatches == 0) {
                    self.$(".search_docu_navigation").addClass("knowsystem_hidden");
                }
                else {
                    self.$(".search_docu_navigation").removeClass("knowsystem_hidden");
                };
            });
        };
    },
    /*
        The mouse click event method to clear search
    */
    _onDocuClearSearch: function(event) {
        this.$("#documentation_content")[0].innerHTML = this.safeContent; 
        this.$("#docu_search_key")[0].value = "";
        this.$("#docu_search_results").addClass("knowsystem_hidden");
    },
    /*
        The mouse click event to scroll to the next found key
    */
    _onNextSearchResult: function(event) {
        var self = this;
        self.$(".docu_search_highlight").removeClass("docu_search_highlight_active");
        if (self.searchResults && self.searchResults.length) {           
            if (self.activeSearchKey != -1) {
                self.activeSearchKey = self.activeSearchKey + 1;
                if (self.activeSearchKey > self.searchResults.length-1) {self.activeSearchKey = 0;};
            }
            else {self.activeSearchKey = 0;                    };
            $("html,body").animate({scrollTop: self.searchResults[self.activeSearchKey]-300}, 400);
            self.$("#"+self.searchIDs[self.activeSearchKey]).addClass("docu_search_highlight_active");
        };
    },
    /*
        The mouse click event to scroll to the previous found key
    */
    _onPreviousSearchResult: function(event) {
        var self = this;
        self.$(".docu_search_highlight").removeClass("docu_search_highlight_active");
        if (self.searchResults && self.searchResults.length) {           
            if (self.activeSearchKey != -1) {
                self.activeSearchKey = self.activeSearchKey - 1;
                if (self.activeSearchKey < 0) {self.activeSearchKey = self.searchResults.length-1;};
            }
            else {self.activeSearchKey = self.searchResults.length-1;                    };
            $("html,body").animate({scrollTop: self.searchResults[self.activeSearchKey]-300}, 400);
            self.$("#"+self.searchIDs[self.activeSearchKey]).addClass("docu_search_highlight_active");
        };
    },
});

/*
 * Introduce own widget for portal searchbar
*/
publicWidget.registry.portalSearchDocPanel = publicWidget.Widget.extend({
    selector: '.o_portal_search_panel_docs',
    events: {
        'click .dropdown-item': '_onDropdownItemClick',
    },

    /**
     * @override
     */
    start: function () {
        var def = this._super.apply(this, arguments);
        this._adaptSearchLabel(this.$('.dropdown-item.active'));
        return def;
    },
    /**
     * @private
     */
    _adaptSearchLabel: function (elem) {
        var $label = $(elem).clone();
        $label.find('span.nolabel').remove();
        this.$('input[name="search"]').attr('placeholder', $label.text().trim());
    },
    /**
     * @private
     */
    _onDropdownItemClick: function (ev) {
        ev.preventDefault();
        var $item = $(ev.currentTarget);
        $item.closest('.dropdown-menu').find('.dropdown-item').removeClass('active');
        $item.addClass('active');

        this._adaptSearchLabel(ev.currentTarget);
    },
});
