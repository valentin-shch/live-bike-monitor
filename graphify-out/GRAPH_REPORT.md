# Graph Report - live-bike-monitor  (2026-11-23)

## Corpus Check
- 53 files · ~75,171 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 22 file(s) not represented in the graph (top: .pbf 15, (none) 3, .css 2)

## Summary
- 3662 nodes · 11236 edges · 183 communities (146 shown, 37 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 723 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `85e39718`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_detect.py
- fetch.py
- HttpError
- run.py
- pandas
- Bicing live: a bike-share monitor that runs without me
- test_skeleton.py
- test_api.py
- Repository
- test_notify.py
- weather.py
- site.js
- test_pages.py
- __
- maplibre-gl-worker.mjs
- u
- draw
- I
- xe
- concat
- n
- screenPointToLocation
- push
- writeMessage
- emplaceBack
- get
- update
- qm
- some
- concat
- tilesIn
- nw
- pg
- reset
- evaluate
- fire
- _checkLoaded
- clone
- ov
- constructor
- projectTileCoordinates
- pmtiles.js
- L
- s
- gl
- loadTile
- po
- parse
- eD
- push
- sf
- emplaceBack
- ay
- w
- createIndex
- cr
- resize
- hx
- remove
- destroy
- constructor
- readVarint
- add
- subdividePolygonInternal
- map.js
- parse
- evaluate
- r
- fromLngLat
- sendAsync
- getSource
- upload
- _createTinySDF
- get
- bS
- fb
- readPackedEnd
- addBucket
- _onWorkerUpdateResult
- _applyGlobalStateChanges
- upload
- O
- scheduleSegment
- n
- S
- i
- disable
- updatePaintArrays
- I
- vm
- l
- getChildren
- lngLatFromWorld
- _forEachCell
- Nc
- bc
- fire
- update
- start
- ti
- _build
- updatePaintArrays
- _executeRelevantHandler
- serialize
- bp
- xv
- LICENSE-basemaps.md
- off
- addTo
- eachChild
- getValueFromBuffer
- lb
- qe
- ping
- setDOMContent
- replace
- j
- recalculate
- du
- _getByteView
- layout
- angleWith
- commit
- freshBind
- _next
- rD
- _getClusterMaxZoom
- getPoint
- _handleSpecialPaintPropertyUpdate
- overwriteGetter
- isAllowedAttribute
- jg
- setSourceProperty
- pop
- paint
- _forEachCell
- de
- yg
- z
- distanceToTile2d
- fu
- he
- _n
- empty
- ee
- extend
- _handleSpecialPaintPropertyUpdate
- Kp
- patchUpdatedImage
- cloneImages
- _drainInertiaBuffer
- hb
- _getAndRemoveByKey
- getClusterOptions
- getDEMElevation
- ja
- layout
- ma
- padding
- setConstrainOverride
- within
- _idx
- bn
- _deserializeCollisionBoxesForSymbol
- getUniforms
- getGeometries
- initializeIndex
- _invoke
- ja
- rn
- Xl
- areTilesLoaded
- getMaxBounds
- setConstantDashPositions
- eu
- setConstantDashPositions
- setConstantPatternPositions

## God Nodes (most connected - your core abstractions)
1. `__` - 1964 edges
2. `constructor()` - 207 edges
3. `push()` - 179 edges
4. `push()` - 162 edges
5. `get()` - 123 edges
6. `n()` - 96 edges
7. `constructor()` - 80 edges
8. `r()` - 79 edges
9. `get()` - 74 edges
10. `fire()` - 72 edges

## Surprising Connections (you probably didn't know these)
- `timelapse()` --indirect_call--> `station_order()`  [INFERRED]
  pages/build.py → api/data.py
- `test_station_detail_has_its_history()` --uses--> `StationDetail`  [INFERRED]
  tests/test_api.py → api/models.py
- `test_empty_by_hour_uses_madrid_hours_and_renting_stations_only()` --uses--> `EmptyByHour`  [INFERRED]
  tests/test_api.py → api/models.py
- `test_empty_station_list_rejects_the_snapshot()` --uses--> `SchemaError`  [INFERRED]
  tests/test_fetch.py → collector/fetch.py
- `test_field_renamed_everywhere_rejects_the_snapshot()` --uses--> `SchemaError`  [INFERRED]
  tests/test_fetch.py → collector/fetch.py

## Import Cycles
- None detected.

## Communities (183 total, 37 thin omitted)

### Community 0 - "test_detect.py"
Cohesion: 0.10
Nodes (39): classify(), confirmed_episodes(), detect_events(), _episodes(), feed_checks(), merge_events(), as_tuples(), at() (+31 more)

### Community 1 - "fetch.py"
Cohesion: 0.12
Nodes (31): Discovery, DiscoveryData, _english(), Envelope, _feed_url(), FeedLink, FeedResult, fetch_feeds() (+23 more)

### Community 2 - "HttpError"
Cohesion: 0.08
Nodes (14): HttpClient, HttpError, FakeAdapter, make_client(), _make(), test_404_is_not_retried(), test_backoff_waits_stay_between_half_and_full_ceiling(), test_each_wait_is_at_least_as_long_as_the_previous() (+6 more)

### Community 3 - "run.py"
Cohesion: 0.07
Nodes (50): collect(), main(), run(), update_events(), alerts_sent_path(), apply_retention(), events_path(), hourly_path() (+42 more)

### Community 4 - "pandas"
Cohesion: 0.19
Nodes (18): collection_events(), coverage(), _last_run_per_window(), read_runs(), runs_path(), weather_events(), window_report(), write_run() (+10 more)

### Community 5 - "Bicing live: a bike-share monitor that runs without me"
Cohesion: 0.17
Nodes (10): Bicing live: a bike-share monitor that runs without me, Honest limits, How it runs without me, Key decisions, Next steps, Run it locally, Bicing station data (Barcelona), Data sources (+2 more)

### Community 8 - "test_api.py"
Cohesion: 0.07
Nodes (31): as_records(), renting_hours(), station_order(), main(), openapi_text(), create_app(), empty_by_hour(), get_station() (+23 more)

### Community 10 - "test_notify.py"
Cohesion: 0.07
Nodes (38): _batches(), configured_notifiers(), _event(), message(), pending_alerts(), send_alerts(), sign(), SlackNotifier (+30 more)

### Community 11 - "weather.py"
Cohesion: 0.12
Nodes (24): SchemaError, bike_days(), fetch_weather(), Forecast, Hourly, is_due(), last_complete_hour(), past_days_needed() (+16 more)

### Community 13 - "test_pages.py"
Cohesion: 0.07
Nodes (41): api_reference(), build(), empty_heatmap(), event_cards(), format_duration(), headline(), health_section(), local_time() (+33 more)

### Community 18 - "__"
Cohesion: 0.01
Nodes (56): __, ai(), bg, bindRTT(), Cf(), ch, Ci, da (+48 more)

### Community 19 - "maplibre-gl-worker.mjs"
Cohesion: 0.01
Nodes (39): Qi(), Ae, Al, aS, au, dv, Ed, fm (+31 more)

### Community 20 - "u"
Cohesion: 0.05
Nodes (98): add(), addClassName(), af(), ah(), ak(), anchorPoint(), apply(), bd() (+90 more)

### Community 21 - "draw"
Cohesion: 0.09
Nodes (73): an, bind(), Bm, bn(), clearStencil(), cn(), colorModeForRenderPass(), constantOr() (+65 more)

### Community 22 - "I"
Cohesion: 0.05
Nodes (69): adjustAntiMeridian(), applyTerrainChange(), applyTransformChange(), applyUpdatedTransform(), calculateAnchoredCameraOptions(), cameraForBounds(), clampCenterToGround(), coalesceChanges() (+61 more)

### Community 23 - "xe"
Cohesion: 0.06
Nodes (67): allowVariableZoom(), at(), be(), bk(), calculateCameraOptionsFromTo(), calculateCenterFromCameraLngLatAlt(), cameraPosition(), _centerAlongView() (+59 more)

### Community 24 - "concat"
Cohesion: 0.05
Nodes (63): ar(), as(), bc(), C(), concat(), cr(), cs(), dc() (+55 more)

### Community 25 - "n"
Cohesion: 0.07
Nodes (60): aa(), ac(), ao(), bj(), bw(), ca(), cc(), co() (+52 more)

### Community 26 - "screenPointToLocation"
Cohesion: 0.05
Nodes (60): _applyChanges(), captureRotationPivot(), _commitFrame(), _computePreZoomAroundLoc(), _coordinateClipPoint(), coordinatePoint(), df(), distSqr() (+52 more)

### Community 27 - "push"
Cohesion: 0.04
Nodes (58): addImages(), addSymbols(), addToLineVertexArray(), addToSortKeyRanges(), Ap(), bf(), by(), cj() (+50 more)

### Community 28 - "writeMessage"
Cohesion: 0.05
Nodes (58): ah, applyGlobalStateChange(), dh(), getGlobalStateRefs(), getLayoutAffectingGlobalStateRefs(), getPaintAffectingGlobalStateRefs(), Ih(), jh() (+50 more)

### Community 29 - "emplaceBack"
Cohesion: 0.08
Nodes (55): _addCollisionDebugVertex(), addCollisionDebugVertices(), Aj(), av(), _calcMatrices(), _clearMatrixCaches(), clearNearFarZOverride(), dt() (+47 more)

### Community 30 - "get"
Cohesion: 0.07
Nodes (55): A(), addIndicesForPlacedSymbol(), attemptAnchorPlacement(), bx(), calculateFogMatrix(), calculatePosMatrix(), CD(), clear() (+47 more)

### Community 31 - "update"
Cohesion: 0.05
Nodes (53): acquireRTT(), anyTilesAfterTime(), beginFrame(), continuePlacement(), crossFadingFactor(), ct(), d(), dh() (+45 more)

### Community 32 - "qm"
Cohesion: 0.06
Nodes (49): b(), bbox(), checkSubtype(), _ensureNoPoleVertices(), error(), _fillPoles(), _generateInterEdgeVertices(), _generateIntraEdgeVertices() (+41 more)

### Community 33 - "some"
Cohesion: 0.05
Nodes (48): al(), cl(), completeTask(), _dataHandler(), _downloadFontFile(), ei(), el(), Fl() (+40 more)

### Community 34 - "concat"
Cohesion: 0.08
Nodes (47): Li(), aa(), ba(), bi(), ca(), concat(), da(), ea() (+39 more)

### Community 35 - "tilesIn"
Cohesion: 0.06
Nodes (46): allowWorldCopies(), au(), cg(), covers(), empty(), expandBy(), extend(), feature() (+38 more)

### Community 36 - "nw"
Cohesion: 0.07
Nodes (45): aw(), bt(), containsMaxSafeIntegerValues(), containsPolygonGeometry(), cw(), decode(), decodeDictionary(), dw() (+37 more)

### Community 37 - "pg"
Cohesion: 0.07
Nodes (45): Vm, addImageSection(), addTextSection(), ag(), _appendSection(), calculateGlyphDependencies(), cg(), determineLineBreaks() (+37 more)

### Community 38 - "reset"
Cohesion: 0.08
Nodes (44): addCurrentVertex(), addHalfVertex(), addLine(), angleTo(), _calculateTransform(), _clearLongPress(), contextmenu(), dblclick() (+36 more)

### Community 39 - "evaluate"
Cohesion: 0.08
Nodes (43): addDebugCollisionBoxes(), addFeature(), addFeatures(), addLineDashDependencies(), bp(), _calculate(), createArrays(), destroyDebugData() (+35 more)

### Community 40 - "fire"
Cohesion: 0.07
Nodes (42): addControl(), addImage(), addSource(), _afterImageUpdated(), _createStyleImage(), _finishLoading(), fire(), getDefaultPosition() (+34 more)

### Community 41 - "_checkLoaded"
Cohesion: 0.10
Nodes (42): addLayer(), addSprite(), _applyProjection(), _checkLoaded(), getFilter(), getLayer(), getLayoutProperty(), _getOperationsToPerform() (+34 more)

### Community 42 - "clone"
Cohesion: 0.08
Nodes (39): addCurrentVertex(), addHalfVertex(), addLine(), addToLineVertexArray(), angleWith(), angleWithSep(), at(), Cc() (+31 more)

### Community 43 - "ov"
Cohesion: 0.08
Nodes (38): addImageSection(), addTextSection(), Ag(), _appendSection(), bv(), calculateGlyphDependencies(), cv(), determineLineBreaks() (+30 more)

### Community 44 - "constructor"
Cohesion: 0.06
Nodes (37): _blockedByActive(), ck(), constructor(), contains(), _createButton(), _createCanvas(), distanceTo(), finish() (+29 more)

### Community 45 - "projectTileCoordinates"
Cohesion: 0.07
Nodes (35): aD(), backfillBorder(), destruct(), difference(), ex(), Fb(), getAllIds(), getRenderableIds() (+27 more)

### Community 46 - "pmtiles.js"
Cohesion: 0.12
Nodes (33): add(), At(), b(), Be(), bt(), constructor(), $e(), Fe() (+25 more)

### Community 47 - "L"
Cohesion: 0.08
Nodes (31): addDash(), addRegularDash(), addRoundDash(), cb(), _declareFontFace(), dispatchRenderCallbacks(), _getCRSParameters(), getDash() (+23 more)

### Community 48 - "s"
Cohesion: 0.10
Nodes (31): am(), _circleAndRectCollide(), _circlesCollide(), cm(), Cp(), createNewSegment(), dp(), getOrCreateLatestSegment() (+23 more)

### Community 49 - "gl"
Cohesion: 0.09
Nodes (30): Bl(), _colorRampChanged(), _createColorRamp(), createNewSegment(), forceNewSegmentOnNextPrepare(), getColorRampTextures(), getOrCreateLatestSegment(), getUnpackVector() (+22 more)

### Community 50 - "loadTile"
Cohesion: 0.10
Nodes (29): _addTerrainIdealTiles(), _addTile(), _afterTileLoadWorkerResponse(), eb(), findTileInCaches(), getByKey(), _getNeighboringTiles(), _getOverzoomParameters() (+21 more)

### Community 51 - "po"
Cohesion: 0.09
Nodes (27): abort(), co(), completeTask(), containsMaxSafeIntegerValues(), copy(), deserialize(), dl(), fl() (+19 more)

### Community 52 - "parse"
Cohesion: 0.11
Nodes (26): Ba(), bi(), bo(), br, bs(), canonicalID(), eachChild(), geometry() (+18 more)

### Community 53 - "eD"
Cohesion: 0.10
Nodes (26): children(), _cleanUpRasterTiles(), _cleanUpVectorTiles(), clearSymbolFadeHold(), _clearTileReloadTimer(), eD(), getExpiryTimeout(), getLoadedTile() (+18 more)

### Community 54 - "push"
Cohesion: 0.10
Nodes (26): A, angleTo(), defines(), eg(), _generateOutline(), getBinderUniforms(), getSortedSymbolIndexes(), hg() (+18 more)

### Community 55 - "sf"
Cohesion: 0.10
Nodes (26): addTileFeatures(), af(), bf(), cf(), cp(), df(), Ef(), f() (+18 more)

### Community 56 - "emplaceBack"
Cohesion: 0.18
Nodes (24): emplaceBack(), eo(), $h(), loadVectorTile(), nh(), b(), d(), _e() (+16 more)

### Community 57 - "ay"
Cohesion: 0.10
Nodes (23): Av(), ay(), bv(), Cv(), Ev(), Gv(), gy(), iy() (+15 more)

### Community 58 - "w"
Cohesion: 0.14
Nodes (22): addLayer(), ao(), ce(), createTree(), _filterGeoJSON(), finish(), _finishRequestTiming(), _getEtagUnmodifiedResult() (+14 more)

### Community 59 - "createIndex"
Cohesion: 0.13
Nodes (21): ap(), clipToWorld(), createIndex(), dp(), getClusters(), getClustersAcrossEdge(), getClustersInRange(), getClustersInternal() (+13 more)

### Community 60 - "cr"
Cohesion: 0.19
Nodes (21): ar(), br(), cr(), distance(), dr(), fr(), gr(), hr() (+13 more)

### Community 61 - "resize"
Cohesion: 0.14
Nodes (18): _containerDimensions(), freeBufferAfterUpload(), _getClampedPixelRatio(), getPixelRatio(), _getUIString(), Ld, redraw(), _refreshViews() (+10 more)

### Community 62 - "hx"
Cohesion: 0.16
Nodes (18): ax(), cx(), dx(), eS(), gx(), hb(), hx(), iS() (+10 more)

### Community 63 - "remove"
Cohesion: 0.13
Nodes (17): _cleanupContainer(), _clearWatch(), filter(), getRTLTextPluginStatus(), _invoke(), isOpen(), jE(), ni (+9 more)

### Community 64 - "destroy"
Cohesion: 0.15
Nodes (17): clearRTTPool(), _clearSource(), clearTextures(), clearTiles(), destroy(), destroyRTTResources(), _disposeTexture(), onRemove() (+9 more)

### Community 65 - "constructor"
Cohesion: 0.13
Nodes (17): abortTile(), addImages(), constructor(), _getAvailableImages(), getClusterChildren(), _getDEMWorkerSource(), _getGlobalState(), _getLayerIndex() (+9 more)

### Community 66 - "readVarint"
Cohesion: 0.18
Nodes (17): ad(), bbox(), decode(), Hs, loadGeometry(), nextField(), qs, readBoolean() (+9 more)

### Community 67 - "add"
Cohesion: 0.18
Nodes (17): add(), b(), Bx(), Cb(), db(), filterUpdate(), gb(), has() (+9 more)

### Community 68 - "subdividePolygonInternal"
Cohesion: 0.15
Nodes (17): _ensureNoPoleVertices(), _fillPoles(), _generateInterEdgeVertices(), _generateIntraEdgeVertices(), _generatePoleQuad(), _getKey(), _handlePoles(), _initializeVertices() (+9 more)

### Community 69 - "map.js"
Cohesion: 0.18
Nodes (14): bounds(), color(), COLORS, COVERED, css, data, madrid, start() (+6 more)

### Community 70 - "parse"
Cohesion: 0.17
Nodes (16): Ce(), checkSubtype(), ci(), createBucket(), E(), encode(), error(), hasOffscreenPass() (+8 more)

### Community 71 - "evaluate"
Cohesion: 0.20
Nodes (16): io(), _calculate(), cm, dt(), Er(), evaluate(), geometry(), interpolate() (+8 more)

### Community 72 - "r"
Cohesion: 0.15
Nodes (16): bu(), ch(), di(), fh(), interpolationFactor(), le(), Mt(), r() (+8 more)

### Community 73 - "fromLngLat"
Cohesion: 0.12
Nodes (16): Cd(), convert(), fd(), fromLngLat(), gd(), hd(), md(), meterInMercatorCoordinateUnits() (+8 more)

### Community 74 - "sendAsync"
Cohesion: 0.14
Nodes (15): abortTile(), broadcast(), buildActors(), buildActorsInBackground(), getActors(), getBuiltActors(), getClusterChildren(), getClusterExpansionZoom() (+7 more)

### Community 75 - "getSource"
Cohesion: 0.13
Nodes (15): bb(), getFeatureState(), getMaxValue(), getSource(), hasLayer(), initializeTileState(), mg(), queryRadius() (+7 more)

### Community 76 - "upload"
Cohesion: 0.18
Nodes (15): _buildSkirts(), createIndexBuffer(), createVertexBuffer(), fj(), getBinderAttributes(), getMesh(), _getMeshKey(), getTerrainMesh() (+7 more)

### Community 77 - "_createTinySDF"
Cohesion: 0.18
Nodes (15): _charUsesLocalIdeographFontFamily(), _createGlyph(), _createTinySDF(), _downloadAndCacheRangePromise(), _drawAlternateGlyph(), _drawGlyph(), _fontStyle(), _fontWeight() (+7 more)

### Community 78 - "get"
Cohesion: 0.21
Nodes (15): addIndicesForPlacedSymbol(), addLineDashDependencies(), clear(), factory(), fromString(), get(), hasIconData(), hasLineDasharray() (+7 more)

### Community 79 - "bS"
Cohesion: 0.15
Nodes (15): bS(), cy(), dS(), getBuffer(), jb(), kb(), lS(), ly() (+7 more)

### Community 80 - "fb"
Cohesion: 0.19
Nodes (15): dy(), fb(), fy(), hy(), increment(), jy(), nb, pb() (+7 more)

### Community 81 - "readPackedEnd"
Cohesion: 0.13
Nodes (15): readDouble(), readFixed32(), readFixed64(), readFloat(), readPackedBoolean(), readPackedDouble(), readPackedEnd(), readPackedFixed32() (+7 more)

### Community 82 - "addBucket"
Cohesion: 0.14
Nodes (14): addBucket(), _areDescendentsComplete(), findMatches(), findMatchesForIndexedEntry(), findMatchesForNonIndexedEntry(), generate(), getCrossTileIDsLists(), _getLoadedDescendents() (+6 more)

### Community 83 - "_onWorkerUpdateResult"
Cohesion: 0.14
Nodes (14): _applyDiffToSource(), _applyResourceTiming(), ax(), cx(), dx(), fx(), _getShouldReloadTileOptions(), lx() (+6 more)

### Community 84 - "_applyGlobalStateChanges"
Cohesion: 0.19
Nodes (14): applyGlobalStateChange(), _applyGlobalStateChanges(), _createLayers(), getGlobalStateRefs(), getLayoutAffectingGlobalStateRefs(), getPaintAffectingGlobalStateRefs(), getVisibilityAffectingGlobalStateRefs(), readsGlobalState() (+6 more)

### Community 85 - "upload"
Cohesion: 0.15
Nodes (14): _addCollisionDebugVertex(), addCollisionDebugVertices(), addDebugCollisionBoxes(), destroy(), destroyDebugData(), generateCollisionDebugBuffers(), getBinderAttributes(), getVertexAttributes() (+6 more)

### Community 86 - "O"
Cohesion: 0.18
Nodes (14): addFeature(), Bt(), Dc(), _generateSideFaces(), getGranularityForZoomLevel(), Ht(), jg(), kg() (+6 more)

### Community 87 - "scheduleSegment"
Cohesion: 0.23
Nodes (13): _cancelRenderFrame(), _deliverPendingEvents(), _finishSegment(), fireAfterQueued(), interrupt(), isContinuedBy(), _queueEndEvents(), _queueFrameEvents() (+5 more)

### Community 88 - "n"
Cohesion: 0.22
Nodes (13): compare(), dn(), fn(), getClusterLeaves(), hn(), mn(), n(), oC() (+5 more)

### Community 89 - "S"
Cohesion: 0.22
Nodes (13): cS(), eb, ec(), fS(), ob(), oS(), S(), sb() (+5 more)

### Community 90 - "i"
Cohesion: 0.18
Nodes (13): ct(), it(), jx(), kf(), lt, m(), ot(), pm() (+5 more)

### Community 91 - "disable"
Cohesion: 0.20
Nodes (12): _destroyUI(), disable(), enable(), _exitFullscreen(), _getTitle(), _handleFullscreenChange(), _isFullscreen(), _requestFullscreen() (+4 more)

### Community 92 - "updatePaintArrays"
Cohesion: 0.21
Nodes (12): ac(), emplace(), feature(), getPositionIds(), getPositions(), Gs(), populatePaintArray(), populatePaintArrays() (+4 more)

### Community 93 - "I"
Cohesion: 0.18
Nodes (12): addFeatures(), constantOr(), createArrays(), detectSdfPatterns(), et(), I, km(), recordSdfPattern() (+4 more)

### Community 94 - "vm"
Cohesion: 0.17
Nodes (12): am(), bm(), gm(), hm(), mm(), nm(), rm(), segment() (+4 more)

### Community 95 - "l"
Cohesion: 0.20
Nodes (12): anchorPoint(), bg(), containsPolygonGeometry(), ex(), geometryType(), getTilePoint(), getVertex(), l() (+4 more)

### Community 96 - "getChildren"
Cohesion: 0.17
Nodes (12): appendLeaves(), cluster(), getChildren(), getClusterExpansionZoom(), getData(), getLeaves(), getOriginId(), getOriginZoom() (+4 more)

### Community 97 - "lngLatFromWorld"
Cohesion: 0.21
Nodes (12): _findLatitudeLimit(), _finiteInverse(), forward(), hasLngLat(), _inverse(), _inverseTowardCenter(), latitudeRange(), lngLatFromWorld() (+4 more)

### Community 98 - "_forEachCell"
Cohesion: 0.20
Nodes (10): _convertFromCellCoord(), _convertToCellCoord(), _convertToXCellCoord(), _convertToYCellCoord(), _forEachCell(), hitTestCircle(), insert(), insertCircle() (+2 more)

### Community 99 - "Nc"
Cohesion: 0.31
Nodes (10): fc(), Hs(), jc(), kc(), Mc(), Nc(), Pc(), queryIntersectsFeature() (+2 more)

### Community 100 - "bc"
Cohesion: 0.24
Nodes (10): bc(), expandBy(), getId(), loadMatchingFeature(), loadVTLayers(), lookupSymbolFeatures(), query(), shrinkBy() (+2 more)

### Community 101 - "fire"
Cohesion: 0.27
Nodes (10): bo(), fire(), _handleOverridablePaintPropertyUpdate(), isDataDriven(), listens(), recalculateVisibility(), setLayoutProperty(), setPaintProperty() (+2 more)

### Community 102 - "update"
Cohesion: 0.24
Nodes (10): generateMipmap(), getMaxValue(), hc(), hl(), replace(), update(), _updateDomImage(), _updateRawData() (+2 more)

### Community 103 - "start"
Cohesion: 0.22
Nodes (9): acquire(), _addDefaultHandlers(), getCanvasContainer(), isMoving(), isZooming(), ml(), pl(), start() (+1 more)

### Community 104 - "ti"
Cohesion: 0.25
Nodes (9): bind(), ei(), ey(), ft(), qi(), _queryCell(), ti(), c() (+1 more)

### Community 105 - "_build"
Cohesion: 0.25
Nodes (8): _build(), _createElevationSampler(), getIndex(), getSampler(), sample(), sampleBilinear(), unpack(), _unpackAtIndex()

### Community 106 - "updatePaintArrays"
Cohesion: 0.36
Nodes (8): emplace(), getPositionIds(), getPositions(), populatePaintArray(), _setPaintValue(), _setPaintValues(), updatePaintArray(), updatePaintArrays()

### Community 107 - "_executeRelevantHandler"
Cohesion: 0.36
Nodes (8): endMove(), _executeRelevantHandler(), _isOneFingerTouch(), _isSameTouchEvent(), isValidEndEvent(), isValidMoveEvent(), isValidStartEvent(), startMove()

### Community 108 - "serialize"
Cohesion: 0.33
Nodes (7): getTransition(), serialize(), _serializeByIds(), _serializedAllLayers(), setState(), toArrayBuffer(), _updateWorkerLayers()

### Community 109 - "bp"
Cohesion: 0.38
Nodes (7): bp(), gp(), hp(), _p(), vp(), xp(), yp()

### Community 110 - "xv"
Cohesion: 0.29
Nodes (7): Fv(), Hv(), Nv(), Pv(), Rv(), xv(), zv()

### Community 111 - "LICENSE-basemaps.md"
Cohesion: 0.33
Nodes (5): Code Licenses and Attribution, The BSD 3-Clause License (BSD-3-Clause), The MIT License (MIT), Tile Schema, Visual Design

### Community 112 - "off"
Cohesion: 0.33
Nodes (6): _addDelegatedListener(), getData(), off(), offTemp(), once(), _removeDelegatedListener()

### Community 113 - "addTo"
Cohesion: 0.47
Nodes (6): addTo(), _endKeyboardDrag(), setDraggable(), setPopup(), _updateAccessibilityRole(), _updateTabIndex()

### Community 114 - "eachChild"
Cohesion: 0.33
Nodes (6): ai(), eachChild(), Gi(), ki(), si(), xi()

### Community 115 - "getValueFromBuffer"
Cohesion: 0.33
Nodes (6): bb(), decodeDictionary(), getValueFromBuffer(), offsetToLengthBuffer(), yb(), yy()

### Community 116 - "lb"
Cohesion: 0.47
Nodes (6): by(), ib, ky(), lb(), vb, zy()

### Community 117 - "qe"
Cohesion: 0.33
Nodes (6): hcl(), lab(), overwriteGetter(), qe(), rgb(), Ye()

### Community 118 - "ping"
Cohesion: 0.40
Nodes (5): answersPing(), ensureWorkers(), ensureWorkersInternal(), ping(), watchWorkers()

### Community 119 - "setDOMContent"
Cohesion: 0.40
Nodes (5): _createCloseButton(), _focusFirstElement(), setDOMContent(), setHTML(), setText()

### Community 120 - "replace"
Cohesion: 0.40
Nodes (5): getHashString(), Py(), replace(), wh(), Yd()

### Community 121 - "j"
Cohesion: 0.50
Nodes (5): addSymbols(), addToSortKeyRanges(), C(), j(), u()

### Community 122 - "recalculate"
Cohesion: 0.40
Nodes (5): crossFadingFactor(), getCrossfadeParameters(), hasPaintOverride(), recalculate(), _setPaintOverrides()

### Community 123 - "du"
Cohesion: 0.40
Nodes (5): cu, du(), fu(), ou, su

### Community 124 - "_getByteView"
Cohesion: 0.40
Nodes (5): _getByteView(), getPixels(), sampleBilinear(), unpack(), _unpackAtIndex()

### Community 125 - "layout"
Cohesion: 0.40
Nodes (5): layout(), Ld(), qu(), tl(), zp()

### Community 126 - "angleWith"
Cohesion: 0.50
Nodes (4): angleWith(), angleWithSep(), Jp, qp

### Community 127 - "commit"
Cohesion: 0.50
Nodes (4): commit(), stillRecent(), symbolFadeChange(), zoomAdjustment()

### Community 128 - "freshBind"
Cohesion: 0.50
Nodes (4): createVertexArray(), enableAttributes(), freshBind(), setVertexAttribPointers()

### Community 129 - "_next"
Cohesion: 0.50
Nodes (4): flush(), isIdle(), _next(), _send()

### Community 130 - "rD"
Cohesion: 0.50
Nodes (4): getAllTiles(), hasTransition(), hasTransitions(), rD()

### Community 131 - "_getClusterMaxZoom"
Cohesion: 0.50
Nodes (4): _getClusterMaxZoom(), _getWaitingWorkerChange(), _pixelsToTileUnits(), setClusterOptions()

### Community 132 - "getPoint"
Cohesion: 0.67
Nodes (4): getPoint(), getScale(), mousePos(), touchPos()

### Community 133 - "_handleSpecialPaintPropertyUpdate"
Cohesion: 0.50
Nodes (4): gradientExpression(), _handleSpecialPaintPropertyUpdate(), ps(), _updateColorRamp()

### Community 134 - "overwriteGetter"
Cohesion: 0.50
Nodes (4): hcl(), lab(), overwriteGetter(), rgb()

### Community 135 - "isAllowedAttribute"
Cohesion: 0.50
Nodes (4): isAllowedAttribute(), isAllowedElement(), removeDisallowedAttributes(), sanitize()

### Community 136 - "jg"
Cohesion: 0.50
Nodes (4): jg(), qg(), Ug(), zg()

### Community 137 - "setSourceProperty"
Cohesion: 0.50
Nodes (4): setPremultiplyAlpha(), setSourceProperty(), setTiles(), setURL()

### Community 138 - "pop"
Cohesion: 0.50
Nodes (4): Bh(), _down(), pop(), qd()

### Community 139 - "paint"
Cohesion: 0.50
Nodes (4): cl(), paint(), yl(), zd()

### Community 140 - "_forEachCell"
Cohesion: 0.50
Nodes (4): _convertFromCellCoord(), _convertToCellCoord(), _forEachCell(), insert()

### Community 141 - "de"
Cohesion: 0.50
Nodes (4): de(), off(), on(), once()

### Community 142 - "yg"
Cohesion: 0.50
Nodes (4): height(), width(), Xg(), yg()

### Community 143 - "z"
Cohesion: 0.50
Nodes (4): ie(), re(), vr(), z()

### Community 144 - "distanceToTile2d"
Cohesion: 0.67
Nodes (3): distanceToTile2d(), distanceX(), distanceY()

### Community 145 - "fu"
Cohesion: 0.67
Nodes (3): fu(), mu(), pu()

### Community 146 - "he"
Cohesion: 1.00
Nodes (3): he(), intersectsFrustum(), intersectsPlane()

### Community 147 - "_n"
Cohesion: 1.00
Nodes (3): canonicalID(), _n, qn()

### Community 148 - "empty"
Cohesion: 0.67
Nodes (3): covers(), empty(), intersects()

### Community 149 - "ee"
Cohesion: 0.67
Nodes (3): ee(), Fc(), Vc()

### Community 150 - "extend"
Cohesion: 0.67
Nodes (3): extend(), fromPoints(), map()

### Community 151 - "_handleSpecialPaintPropertyUpdate"
Cohesion: 0.67
Nodes (3): gradientExpression(), _handleSpecialPaintPropertyUpdate(), _updateColorRamp()

### Community 152 - "Kp"
Cohesion: 0.67
Nodes (3): Kp(), queryRadius(), Uc()

### Community 153 - "patchUpdatedImage"
Cohesion: 0.67
Nodes (3): patchUpdatedImage(), patchUpdatedImages(), zh()

## Knowledge Gaps
- **91 isolated node(s):** `data`, `css`, `COLORS`, `WORDS`, `madrid` (+86 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 631 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `__` connect `__` to `maplibre-gl-worker.mjs`, `u`, `draw`, `I`, `xe`, `concat`, `n`, `screenPointToLocation`, `push`, `emplaceBack`, `get`, `update`, `qm`, `some`, `concat`, `tilesIn`, `nw`, `pg`, `reset`, `evaluate`, `fire`, `_checkLoaded`, `clone`, `ov`, `constructor`, `projectTileCoordinates`, `L`, `s`, `loadTile`, `parse`, `eD`, `emplaceBack`, `resize`, `remove`, `destroy`, `readVarint`, `map.js`, `parse`, `evaluate`, `sendAsync`, `getSource`, `upload`, `_createTinySDF`, `addBucket`, `_onWorkerUpdateResult`, `_applyGlobalStateChanges`, `O`, `scheduleSegment`, `disable`, `updatePaintArrays`, `_forEachCell`, `Nc`, `bc`, `start`, `_build`, `updatePaintArrays`, `_executeRelevantHandler`, `serialize`, `off`, `addTo`, `ping`, `setDOMContent`, `replace`, `angleWith`, `commit`, `freshBind`, `_next`, `rD`, `_getClusterMaxZoom`, `getPoint`, `_handleSpecialPaintPropertyUpdate`, `overwriteGetter`, `isAllowedAttribute`, `jg`, `setSourceProperty`, `distanceToTile2d`, `fu`, `he`, `cloneImages`, `_drainInertiaBuffer`, `hb`, `_getAndRemoveByKey`, `getClusterOptions`, `getDEMElevation`, `ja`, `layout`, `ma`, `padding`, `setConstrainOverride`, `within`, `Xl`, `areTilesLoaded`, `getMaxBounds`, `setConstantDashPositions`?**
  _High betweenness centrality (0.566) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `__` (e.g. with `aa()` and `ac()`) actually correct?**
  _`__` has 49 INFERRED edges - model-reasoned connections that need verification._
- **What connects `data`, `css`, `COLORS` to the rest of the system?**
  _91 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_detect.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10256410256410256 - nodes in this community are weakly interconnected._
- **Why does `Dc()` connect `O` to `emplaceBack`, `__`, `maplibre-gl-worker.mjs`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `constructor()` (e.g. with `n()` and `r()`) actually correct?**
  _`constructor()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `fetch.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1241565452091768 - nodes in this community are weakly interconnected._