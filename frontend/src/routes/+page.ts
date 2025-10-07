import type { PageLoad } from './$types';

export interface BankAttempt {
	comment_id: string;
	method: string;
	success: boolean;
	timestamp: number;
}

export interface BankData {
	[bankName: string]: BankAttempt[];
}

export const load: PageLoad = async ({ fetch }) => {
	const response = await fetch('/by_bank.json');
	const data: BankData = await response.json();
	return { banks: data };
};
