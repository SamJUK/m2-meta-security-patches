# Magento 2 Meta Package: Security Patches

[![Test on Master](https://github.com/SamJUK/m2-meta-security-patches/actions/workflows/test-master.yml/badge.svg)](https://github.com/SamJUK/m2-meta-security-patches/actions/workflows/test-master.yml)

This repository contains a meta package for applying security patches to Magento 2 installations. The package aggregates various security patches including Adobe's new isolated patches, and emergency out of band patches to ensure that your Magento 2 store remains secure against known vulnerabilities.

The primary reason for using a meta package is to simplify the management and application of multiple security patches. Instead of applying each patch individually to each project, you can install this meta package, which will automatically include all the necessary patches.

Future updates can be handled automatically via Dependabot or Renovate, ensuring that your Magento 2 installation stays up-to-date with the latest security fixes without the manual overhead and cost.

## Requirements

- Magento 2.4.2+ (see [test-matrix.json](test-matrix.json) for full compatibility)
- PHP 7.4+ (version depends on Magento version)
- Composer 2.x

## List of Included Security Patches

We break down the included security patches into a few groups:

### Isolated Security Patches

These are the new approach to regular security updates provided by Adobe.

- TBA

For detailed information on each patch, see the patches in [src/patches/isolated/](src/patches/isolated/).

### Emergency Security Patches

These patches address critical vulnerabilities out of band security issues that require immediate attention:

- **CVE-2024-34102** - CosmicSting vulnerability affecting Magento 2.4.7 and earlier
- **CVE-2025-54236** - Session security vulnerability

For detailed information on each patch, see the patches in [src/patches/emergency/](src/patches/emergency/).

## Installation

To install the meta package, use Composer by running the following command in your Magento 2 root directory:

```bash
composer require samjuk/m2-meta-security-patches:">=2026.02.01"
```

The patches will be automatically applied during installation via [vaimo/composer-patches](https://github.com/vaimo/composer-patches).

## Versioning

The versioning of this meta package follows date based versioning to indicate the release date of the included patches. For example, a version `2024.10.15` indicates that the package was released on October 15, 2024.

## Development

To contribute to the development of this meta package:

1. Clone the repository
2. Make your changes in the `src/` directory
3. Add or update patches in `src/patches/`
4. Update `src/composer.json` with patch configuration
5. Run tests locally with `sh tests/test.sh` (requires Docker)
6. Submit a pull request

## Testing

### Automated Testing

Full E2E tests are run via GitHub Actions:
- **On master/main commits**: Tests run automatically on every push
- **On pull requests**: Add the `run-tests` label to trigger the test suite

The test suite validates the package installation across multiple Magento versions and PHP versions (see [test-matrix.json](tests/test-matrix.json) for the complete matrix).

### Local Testing

You can run the full test suite locally with Docker:

```sh
sh tests/test.sh
```

This will test the package installation across all supported Magento/PHP version combinations. Be aware, this can take a significant amount of disk space and time.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure tests pass locally
5. Submit a pull request
