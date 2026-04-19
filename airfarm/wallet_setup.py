import argparse
import json
import os
import getpass
from wallet_factory import generate_mnemonic, derive_wallets_from_mnemonic, save_encrypted_wallets


def main():
    parser = argparse.ArgumentParser(
        description='Generate deterministic Ethereum wallets from a BIP-39 mnemonic and encrypt the wallet store.'
    )
    parser.add_argument('--mnemonic', help='Existing BIP-39 mnemonic to derive wallets from')
    parser.add_argument('--words', type=int, default=12, choices=[12, 15, 18, 21, 24],
                        help='Mnemonic length if generating a new phrase')
    parser.add_argument('--count', type=int, default=5, help='Number of wallets to derive')
    parser.add_argument('--start-index', type=int, default=0, help='Starting derivation index')
    parser.add_argument('--output', default='data/wallets.enc', help='Encrypted wallet store output path')
    parser.add_argument('--plaintext', action='store_true', help='Also write an optional plaintext wallet JSON file for verification')
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    mnemonic = args.mnemonic or generate_mnemonic(args.words)
    wallets = derive_wallets_from_mnemonic(mnemonic, count=args.count, start_index=args.start_index)

    password = os.getenv('WALLET_STORE_KEY')
    if not password:
        password = getpass.getpass('Enter encryption password for wallet store: ').strip()
    if not password:
        raise ValueError('Wallet store key is required to encrypt wallet data.')

    save_encrypted_wallets(wallets, password, args.output)
    print(f'Encrypted wallet store saved to {args.output}')
    print('Keep your wallet encryption key private. The encrypted store can be loaded at runtime with WALLET_STORE_KEY.')
    print(f'Mnemonic used: {mnemonic}')

    if args.plaintext:
        plaintext_path = os.path.splitext(args.output)[0] + '.json'
        with open(plaintext_path, 'w', encoding='utf-8') as f:
            json.dump({'mnemonic': mnemonic, 'wallets': wallets}, f, indent=2)
        print(f'Plaintext wallet file saved to {plaintext_path} (delete this file after verification)')


if __name__ == '__main__':
    main()
