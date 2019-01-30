var app = angular.module('myApp', []);
app.controller('myCtrl', function($scope, $http) {
	$scope.isLogin = false;
	$scope.memo = '';
	$scope.address = '';

	$scope.login = function() {
		if (!$scope.username) {
			return;
		}
		if(!$scope.password) {
			return;
		}
		data = {
			'username': $scope.username,
			'password': $scope.password
		}
		$http({
			method : "POST",
		  	url : "/login",
		  	data : data,
		}).then(function mySuccess(response) {
			if (response.data.data == 'successfuly') {
				$scope.isLogin = true;
				getNewOrder();
			}
		}, function myError(response) {
			alert(response.data.data);
		});
	}

	function getNewOrder() {
		$http({
			method : "GET",
		  	url : "/new_order",
		}).then(function mySuccess(response) {
			data = response.data;
			$scope.memo = data['memo'];
			$scope.address = data['address'];
			$scope.state = 'Waiting For Payment';
			$scope.timmer = setInterval(checkState, 5000);
		}, function myError(response) {
			alert(response.data.data);
		});
	}

	function checkState() {
		$http({
			method : "GET",
		  	url : "/order_state/"+$scope.memo,
		}).then(function mySuccess(response) {
			data = response.data;
			if (data.state == 'paid') {
				clearInterval($scope.timmer);
				$scope.state = 'Paid Successfuly';
				s = document.getElementsByClassName('waiting');
				s[0].classList.add('successfuly');
				s[0].classList.remove('waiting');
			}
		}, function myError(response) {

		});
	}
});