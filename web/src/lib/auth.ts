import {
	CognitoUserPool,
	CognitoUser,
	AuthenticationDetails,
	CognitoUserAttribute,
	type CognitoUserSession
} from 'amazon-cognito-identity-js';

const POOL_ID = import.meta.env.VITE_COGNITO_USER_POOL_ID || '';
const CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID || '';

let _userPool: CognitoUserPool | null = null;

function getUserPool(): CognitoUserPool {
	if (!_userPool) {
		_userPool = new CognitoUserPool({
			UserPoolId: POOL_ID,
			ClientId: CLIENT_ID
		});
	}
	return _userPool;
}

export function signUp(email: string, password: string): Promise<string> {
	return new Promise((resolve, reject) => {
		const attributes = [new CognitoUserAttribute({ Name: 'email', Value: email })];
		getUserPool().signUp(email, password, attributes, [], (err, result) => {
			if (err) return reject(err);
			resolve(result!.userSub);
		});
	});
}

export function confirmSignUp(email: string, code: string): Promise<void> {
	return new Promise((resolve, reject) => {
		const cognitoUser = new CognitoUser({ Username: email, Pool: getUserPool() });
		cognitoUser.confirmRegistration(code, true, (err) => {
			if (err) return reject(err);
			resolve();
		});
	});
}

export function login(email: string, password: string): Promise<CognitoUserSession> {
	return new Promise((resolve, reject) => {
		const cognitoUser = new CognitoUser({ Username: email, Pool: getUserPool() });
		const authDetails = new AuthenticationDetails({ Username: email, Password: password });
		cognitoUser.authenticateUser(authDetails, {
			onSuccess: (session) => resolve(session),
			onFailure: (err) => reject(err)
		});
	});
}

export function getSession(): Promise<CognitoUserSession | null> {
	return new Promise((resolve) => {
		const cognitoUser = getUserPool().getCurrentUser();
		if (!cognitoUser) return resolve(null);
		cognitoUser.getSession((err: Error | null, session: CognitoUserSession | null) => {
			if (err || !session?.isValid()) return resolve(null);
			resolve(session);
		});
	});
}

export function refreshSession(): Promise<CognitoUserSession | null> {
	return new Promise((resolve) => {
		const cognitoUser = getUserPool().getCurrentUser();
		if (!cognitoUser) return resolve(null);
		cognitoUser.getSession((err: Error | null, session: CognitoUserSession | null) => {
			if (err || !session) return resolve(null);
			const refreshToken = session.getRefreshToken();
			cognitoUser.refreshSession(refreshToken, (refreshErr, newSession) => {
				if (refreshErr) return resolve(null);
				resolve(newSession);
			});
		});
	});
}

export function logout(): void {
	const cognitoUser = getUserPool().getCurrentUser();
	if (cognitoUser) cognitoUser.signOut();
}
