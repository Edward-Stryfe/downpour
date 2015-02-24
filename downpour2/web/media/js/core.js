var transfers = angular.module('transfers', []);

transfers.controller('TransferListView', ['$scope', 'authenticator',
    function($scope, authenticator) {
        authenticator.require().then(
            function(user) {
                $scope.setSection('transfers');
            }
        );
    }
]);

transfers.controller('TransferList', ['$scope', '$http', '$interval', 'authenticator',
    function($scope, $http, $interval, authenticator) {

        var transfers = {};

        $scope.downloads = [];
        $scope.queued = [];
        $scope.uploads = [];
        $scope.completed = [];

        var copy = function(src, dest) {
            for (var attr in src) {
                if (src.hasOwnProperty(attr)) dest[attr] = src[attr];
            }
        };

        var updateList = function(current, next) {

        };

        var update = function() {

            $http.get('/transfers/status' + ($scope.demoMode ? '/demo' : '')).then(
                function(response) {

                    var downloads = [];
                    var queued = [];
                    var uploads = [];
                    var completed = [];

                    angular.forEach(response.data, function(transfer) {

                        if (transfer.id in transfers) {
                            copy(transfer, transfers[transfer.id])
                            transfer = transfers[transfer.id];
                        } else
                            transfers[transfer.id] = transfer;

                        if (transfer.state.state == 'seeding')
                            uploads.push(transfer);
                        else if (transfer.state.state == 'queued')
                            queued.push(transfer);
                        else if (transfer.removed)
                            completed.push(transfer);
                        else
                            downloads.push(transfer);

                    });

                    $scope.downloads = downloads;
                    $scope.queued = queued;
                    $scope.uploads = uploads;
                    $scope.completed = completed;
                    // updateList($scope.downloads, downloads);
                    // updateList($scope.queued, queued);
                    // updateList($scope.uploads, uploads);
                    // updateList($scope.completed, completed);

                }
            );

        }

        update();

        angular.forEach(['start', 'stop', 'remove'], function(action) {
            $scope[action] = function(transfer) {
                if (transfer.state[action]) {
                    $http.post('/transfers/detail/' + transfer.id + '/' + action).then(
                        function(response) {
                            update();
                        },
                        function(response) {
                            update();
                        }
                    );
                }
            }
        });

        var updateInterval = $interval(update, 1000);
        $scope.$on('$destroy', function() {
            $interval.cancel(updateInterval);
        })

    }
]);

transfers.controller('TransferDetail', ['$scope', '$routeParams',
    function($scope, $routeParams) {

    }
]);

transfers.controller('TransferAddURL', ['$scope', '$http', '$q', 'authenticator',
    function($scope, $http, $q, authenticator) {

        $scope.submit = function() {

            return $http({
                method: 'POST',
                url: '/transfers/add/url',
                data: $.param({ 'url': $scope.url }),
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            }).then(
                function(response) {
                    $scope.url = '';
                },
                function(response) {
                    // TODO Display error
                    return $q.reject('Unable to fetch URL');
                }
            );

        };

    }
]);

transfers.controller('TransferAddTorrent', ['$scope',
    function($scope) {

    }
]);

var account = angular.module('account', []);

account.controller('AccountLogin', ['$scope', '$location', 'authenticator',
    function($scope, $location, authenticator) {

        $scope.submit = function() {
            authenticator.login(
                $scope.username, $scope.password
            ).then(
                function(user) {
                    $scope.error = null;
                    $location.path('/');
                },
                function(error) {
                    $scope.error = error;
                }
            );
        };

    }
]);